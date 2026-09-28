"""Use the existing governed Core without adding a second knowledge database.

All lookups are read-only. Staging emits the Core's existing reviewable bundle
format; it never calls ingestion or promotes a Claim on the caller's behalf.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os

from . import index
from .storage import ContractError, Store, key_for


def context(store: Store, identifier: str, query: str, *, entity_id=None, extra_context=None,
            repository=None, explain=None, dsn=None, limit=20, cursor=None,
            scope=None, namespace=None, track=None):
    snap=index._load(store,identifier); manifest=snap['profile']['manifest']
    exact={'minecraft_version':manifest['minecraft'],'loader':manifest['loader'],
           'loader_version':manifest['loader_version'],'namespace':manifest['namespace'],
           'physical_side':manifest['physical_side'],'track':manifest['track']}
    if extra_context is not None:
        if not isinstance(extra_context,dict): raise ContractError('Exact applicability context must be an object')
        for k,v in extra_context.items():
            if k in exact and (type(v) is not type(exact[k]) or v!=exact[k]):
                raise ContractError('Applicability conflict with captured environment: '+k)
        exact.update(extra_context)
    research=index.search(store,identifier,query,limit=limit,cursor=cursor,scope=scope,namespace=namespace,track=track)
    governed={'status':'NOT_REQUESTED','artifact_hash':None,'reason':'No canonical Knowledge Entity ID supplied'}
    connection=None
    if entity_id is not None:
        if not isinstance(entity_id,str) or not entity_id.startswith('ke:'): raise ContractError('Canonical Knowledge Entity ID required')
        try:
            if any(exact[k] in (None,'UNKNOWN','UNRESOLVED') for k in ('minecraft_version','loader','loader_version','namespace','physical_side')):
                raise ContractError('Unresolved environment cannot select trusted guidance')
            if repository is None:
                from ..postgres_repository import PostgresRepository
                value=dsn or os.environ.get('KTHUB_DATABASE_URL')
                if not value: raise ContractError('KTHUB_DATABASE_URL is not configured')
                repository=connection=PostgresRepository.connect(value)
            if explain is None:
                from ..explanation import explain_contextual_guidance
                explain=explain_contextual_guidance
            result=explain(repository,entity_id,context=exact)
            if not isinstance(result,dict): raise ContractError('Core response is not an object')
            # Preserve the entire explanation, including ambiguity and qualifiers, in CAS.
            # Do not replace it with an agent-generated justification or pick a winner.
            artifact=store.put_json(result); store.pin(artifact,'core-guidance:'+artifact)
            governed={'status':'OK','artifact_hash':artifact,'entity_id':entity_id,
                      'candidate_claim_ids':result.get('candidate_claim_ids',[]),
                      'explanation_count':result.get('explanation_count',len(result.get('claim_explanations',[]))),
                      'read_with':'artifact read --hash '+artifact,'selection':'EXACT_EXISTING_CORE'}
        except Exception as exc:  # Backend drivers use their own exception families.
            # Connection exceptions can contain a DSN. Do not include their message.
            governed={'status':'UNAVAILABLE','artifact_hash':None,'error_type':type(exc).__name__,
                      'reason':'Core lookup unavailable or provenance invalid; no trusted fallback'}
        finally:
            if connection is not None:
                try: connection.close()
                except Exception: pass  # Closing a failed read must not hide raw source.
    status='PARTIAL' if governed['status']=='UNAVAILABLE' else research['status']
    return dict(schema_version=1,status=status,profile_id=snap['profile']['profile_id'],
                index_snapshot_id=identifier,exact_context=exact,research=research,governed=governed,
                next_cursor=research['next_cursor'],canonical_writes=0,
                note='Research candidates are not validated guidance. Governed selection is owned by the existing Core.')


def stage_bundle(store: Store, identifier: str, document_ids: list[str], *, summary: str,
                 actor: dict, captured_at: str | None=None, existing_repository=None):
    """Export Source/Snapshot/Evidence/NEW observations in the Core bundle format.

    Each observation belongs to exactly one captured root/snapshot. Its source is
    identified as a local artifact capture, never passed off as upstream author
    intent. Missing original bytes are an error, not synthetic evidence.
    """
    if not isinstance(summary,str) or not summary.strip() or len(summary)>16000:
        raise ContractError('A bounded, nonempty observation summary is required')
    if not isinstance(actor,dict) or actor.get('actor_type') not in ('ai','tool') or set(actor)-{'actor_type','actor_id','version'}:
        raise ContractError('Preserve the actual AI/tool observation creator')
    if not isinstance(document_ids,list) or not document_ids or len(document_ids)>1000 or len(set(document_ids))!=len(document_ids):
        raise ContractError('Select 1..1000 distinct captured documents')
    when=captured_at or datetime.now(timezone.utc).isoformat()
    try:
        timestamp=datetime.fromisoformat(when.replace('Z','+00:00'))
        if timestamp.tzinfo is None: raise ValueError('timezone')
    except (TypeError,ValueError): raise ContractError('captured_at must be an ISO timestamp with timezone') from None
    snap=index._load(store,identifier); p=snap['profile']; docs={d['document_id']:d for d in p['documents']}
    roots={r['id']:r for r in p['roots']}; groups={}
    for doc_id in document_ids:
        if doc_id not in docs: raise ContractError('Document does not belong to this index: '+str(doc_id))
        d=docs[doc_id]; store.read(d['content_hash']); groups.setdefault(d['root_id'],[]).append(d)
    records=[]; pins=[identifier]
    for root_id, selected in groups.items():
        root=roots[root_id]
        origin={'capture_type':'local_artifact','path':root['path'],'root_id':root_id,
                'namespace':root['namespace'],'stage':root['stage']}
        if root.get('source_url'): origin['upstream_url']=root['source_url']
        source_id='src:minecraft:'+key_for(origin)
        snapshot_id='ss:minecraft:'+key_for({'source_id':source_id,'artifact_hash':root['artifact_hash']})
        source={'record_type':'source','id':source_id,'kind':'experiment','origin':origin,
                'acquisition':{'level':'selected-files'},'license':{'state':'UNKNOWN'}}
        snapshot={'record_type':'source_snapshot','id':snapshot_id,'source_id':source_id,
                  'content_hash':root['artifact_hash'],'captured_at':when,
                  'metadata':{'index_snapshot_id':identifier,'root_id':root_id,
                              'original_artifact_hash':root.get('original_artifact_hash'),
                              'profile_id':p['profile_id'],'capture_scope':'selected_documents_from_immutable_root'}}
        records.extend((source,snapshot)); evidence_ids=[]
        for d in selected:
            loc=index.locator(identifier,d); loc.update(type='experiment_artifact',
                url='urn:sha256:'+d['content_hash'],runtime_status='NOT_EXECUTED')
            evidence_id='ev:minecraft:'+key_for({'snapshot':snapshot_id,'locator':loc})
            records.append({'record_type':'evidence','id':evidence_id,'source_id':source_id,
                            'source_snapshot_id':snapshot_id,'locator':loc,'roles':['QUALIFIES'],'observed_at':when})
            evidence_ids.append(evidence_id); pins.append(d['content_hash'])
        obs={'record_type':'staged_observation','source_id':source_id,'summary':summary,
             'evidence_candidate_ids':evidence_ids,'created_by':actor,'status':'NEW'}
        obs['id']='obs:minecraft:'+key_for(obs); records.append(obs)
    if existing_repository is not None:
        retained=[]
        for r in records:
            previous=existing_repository.get(r['id'])
            if previous is None: retained.append(r); continue
            # Reuse already registered immutable evidence. Never rewrite it just to
            # change an observation timestamp; conflicting content is rejected.
            a={k:v for k,v in previous.items() if k not in ('captured_at','observed_at')}
            b={k:v for k,v in r.items() if k not in ('captured_at','observed_at')}
            if a!=b: raise ContractError('Existing Core record differs: '+r['id'])
        records=retained
    if not records: return {'status':'NOT_MODIFIED','canonical_writes':0,'bundle_hash':None}
    b={'bundle_version':'1.0','bundle_id':'bundle:minecraft:'+key_for(records),
       'title':'Minecraft captured-code observations','purpose':'Review only; no claims or identity promotion',
       'domains':['minecraft'],'records':records}
    artifact=store.put_json(b)
    for pin in pins+[artifact]: store.pin(pin,'stage:'+artifact)
    return {'status':'OK','bundle_hash':artifact,'records':len(records),'canonical_writes':0,
            'ingestion':'REQUIRES_EXISTING_CORE_REVIEW'}
