package kneekura.danmaku;

import javafx.animation.AnimationTimer;
import javafx.application.Application;
import javafx.application.ConditionalFeature;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.*;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.scene.paint.Color;
import javafx.scene.paint.PhongMaterial;
import javafx.scene.shape.Box;
import javafx.scene.shape.Sphere;
import javafx.scene.transform.Rotate;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;

/** Multi-track Score preview. Existing PreviewApp remains the v1 single-pattern editor. */
public final class ScorePreviewApp extends Application {
    private Score.Config score = Score.defaults();
    private final Group world = new Group(), particles = new Group(), cameraRig = new Group();
    private final ArrayList<Sphere> pool = new ArrayList<>();
    private final ArrayList<PhongMaterial> materials = new ArrayList<>();
    private final PerspectiveCamera camera = new PerspectiveCamera(true);
    private final Rotate yaw = new Rotate(-35, Rotate.Y_AXIS), pitch = new Rotate(-25, Rotate.X_AXIS);
    private final ListView<String> trackList = new ListView<>();
    private final ComboBox<Pattern.Kind> kind = new ComboBox<>();
    private final ComboBox<Score.Frame> frame = new ComboBox<>();
    private final LinkedHashMap<String, TextField> fields = new LinkedHashMap<>();
    private final TextField nameField = new TextField(), durationField = new TextField();
    private final Label status = new Label(), readout = new Label();
    private final Slider timeline = new Slider(0, 240, 0);
    private final Button play = new Button("▶ 再生");
    private Node playerMarker;
    private double tick, dragX, dragY;
    private long lastNano;
    private boolean playing, updating, inputsValid = true;
    private int selectedTrack;
    private Stage stage;
    private SubScene viewport;

    @Override public void start(Stage stage) {
        this.stage = stage;
        if (!Platform.isSupported(ConditionalFeature.SCENE3D))
            throw new IllegalStateException("JavaFX SCENE3D is unavailable on this graphics environment");
        readStartupScore();
        buildWorld();
        camera.setNearClip(0.05); camera.setFarClip(1000); camera.setFieldOfView(45); camera.setTranslateZ(-46);
        cameraRig.getTransforms().addAll(yaw, pitch); cameraRig.getChildren().add(camera);
        Group sceneRoot = new Group(world, cameraRig, new AmbientLight(Color.WHITE));
        viewport = new SubScene(sceneRoot, 860, 640, true, SceneAntialiasing.BALANCED);
        viewport.setFill(Color.web("#0b1420")); viewport.setCamera(camera);
        StackPane view = new StackPane(viewport);
        viewport.widthProperty().bind(view.widthProperty()); viewport.heightProperty().bind(view.heightProperty());
        viewport.setOnMousePressed(e -> { dragX = e.getSceneX(); dragY = e.getSceneY(); });
        viewport.setOnMouseDragged(e -> {
            double dx = e.getSceneX() - dragX, dy = e.getSceneY() - dragY;
            if (e.isSecondaryButtonDown()) {
                double scale = 2 * Math.abs(camera.getTranslateZ())
                    * Math.tan(Math.toRadians(camera.getFieldOfView()) / 2) / Math.max(1, viewport.getHeight());
                var delta = cameraRig.getLocalToParentTransform().deltaTransform(-dx * scale, -dy * scale, 0);
                cameraRig.setTranslateX(cameraRig.getTranslateX() + delta.getX());
                cameraRig.setTranslateY(cameraRig.getTranslateY() + delta.getY());
                cameraRig.setTranslateZ(cameraRig.getTranslateZ() + delta.getZ());
                e.consume();
            } else if (e.isPrimaryButtonDown()) {
                yaw.setAngle(yaw.getAngle() + dx * 0.35);
                pitch.setAngle(Math.max(-89.9, Math.min(89.9, pitch.getAngle() - dy * 0.35)));
                e.consume();
            }
            dragX = e.getSceneX(); dragY = e.getSceneY();
        });
        viewport.setOnScroll(e -> camera.setTranslateZ(Math.max(-220, Math.min(-6,
            camera.getTranslateZ() + e.getDeltaY() * 0.06))));

        BorderPane root = new BorderPane(view);
        root.setTop(header()); root.setRight(editor()); root.setBottom(transport());
        root.setStyle("-fx-background-color: #14202d; -fx-font-family: 'Yu Gothic UI'; -fx-font-size: 13px;");
        Scene scene = new Scene(root, 1240, 820, true);
        stage.setTitle("KNEEKURA / 弾幕スコア"); stage.setScene(scene);
        stage.setMinWidth(1050); stage.setMinHeight(720);
        stage.iconifiedProperty().addListener((o, old, minimized) -> { if (minimized) setPlaying(false); });
        syncScore(); playerView(); redraw(); stage.show();

        new AnimationTimer() {
            @Override public void handle(long now) {
                if (!playing) { lastNano = 0; return; }
                if (lastNano != 0) {
                    tick = Math.min(score.durationTicks(), tick + (now - lastNano) / 1e9 * 20);
                    redraw();
                    if (tick >= score.durationTicks()) setPlaying(false);
                }
                lastNano = playing ? now : 0;
            }
        }.start();
    }

    private void readStartupScore() {
        List<String> args = getParameters().getRaw();
        if (args.size() >= 2 && args.get(0).equals("--score")) {
            try { score = ScoreJson.read(Files.readString(Path.of(args.get(1)), StandardCharsets.UTF_8)); }
            catch (Exception ex) { throw new IllegalArgumentException("Cannot load score: " + args.get(1), ex); }
        }
    }

    private Node header() {
        Label title = label("Grand Danmaku / Score Mode", "-fx-font-size: 22px; -fx-font-weight: bold;");
        Label note = label("複数Trackを重ね、Player POVで『総統ガストから咲く弾幕』を確認", "-fx-text-fill: #91abc3;");
        VBox box = new VBox(4, title, note); box.setPadding(new Insets(16, 22, 12, 22)); return box;
    }

    private Node editor() {
        VBox pane = new VBox(9); pane.setPadding(new Insets(14)); pane.setPrefWidth(330);
        pane.setStyle("-fx-background-color: #eaf0f5;");
        Label scoreTitle = new Label("Score / Track"); scoreTitle.setStyle("-fx-font-size: 16px; -fx-font-weight: bold;");
        durationField.textProperty().addListener((o,a,b) -> applyFields());
        GridPane scoreGrid = new GridPane(); scoreGrid.setHgap(8); scoreGrid.setVgap(6);
        scoreGrid.add(new Label("Score期間 / tick"),0,0); scoreGrid.add(durationField,1,0);
        trackList.setPrefHeight(130);
        trackList.getSelectionModel().selectedIndexProperty().addListener((o, old, value) -> {
            if (updating || value.intValue() < 0) return;
            selectedTrack = value.intValue(); syncSelectedTrack();
        });

        kind.getItems().setAll(Pattern.Kind.values()); frame.getItems().setAll(Score.Frame.values());
        kind.valueProperty().addListener((o,a,b) -> applyFields());
        frame.valueProperty().addListener((o,a,b) -> applyFields());
        nameField.textProperty().addListener((o,a,b) -> applyFields());

        GridPane grid = new GridPane(); grid.setHgap(8); grid.setVgap(6);
        int row = 0;
        grid.add(new Label("name"),0,row); grid.add(nameField,1,row++);
        grid.add(new Label("frame"),0,row); grid.add(frame,1,row++);
        grid.add(new Label("pattern"),0,row); grid.add(kind,1,row++);
        String[][] rows = {
            {"startTick","開始 tick"},{"endTick","終了 tick"},{"forwardSpeed","前進速度"},{"phaseDeg","位相 °"},
            {"hue","色相 0..360"},{"radius","弾表示半径"},{"bullets","弾数 / burst"},
            {"speed","画面面内速度"},{"intervalTicks","発射間隔 tick"},{"fanAngleDeg","扇角度"},
            {"rotationDegPerSecond","回転 °/秒"},{"elevationDeg","v1仰角"},{"lifetimeTicks","寿命 tick"}
        };
        for (String[] r : rows) {
            TextField field = new TextField(); field.setPrefColumnCount(6); fields.put(r[0], field);
            grid.add(new Label(r[1]),0,row); grid.add(field,1,row++);
            field.textProperty().addListener((o,a,b) -> applyFields());
        }

        Button save = new Button("Score保存"), load = new Button("Score読込");
        save.setOnAction(e -> chooseFile(true)); load.setOnAction(e -> chooseFile(false));
        status.setWrapText(true);
        Label help = new Label(
            "PLAYER_VIEW: Patternの円/螺旋を画面の右・上へ写し、\nforwardSpeedでプレイヤー方向へ進めます。\n" +
            "橙=総統ガスト発射点 / 緑=Player目印(24block)\n" +
            "Player POVでは緑の目印を非表示。\n最大同時弾数 3,000。v1 Pattern JSONは変更しません。");
        help.setWrapText(true); help.setStyle("-fx-text-fill: #526479; -fx-font-size: 11px;");
        pane.getChildren().addAll(scoreTitle, scoreGrid, trackList, new Separator(), grid,
            new HBox(8, save, load), status, help);
        ScrollPane scroll = new ScrollPane(pane); scroll.setFitToWidth(true); scroll.setPrefWidth(332); return scroll;
    }

    private Node transport() {
        play.setOnAction(e -> { if (!playing && tick >= score.durationTicks()) tick = 0; setPlaying(!playing); redraw(); });
        Button reset = new Button("↺ 最初から"), step = new Button("+1 tick");
        reset.setOnAction(e -> seek(0)); step.setOnAction(e -> seek(Math.min(score.durationTicks(), Math.floor(tick) + 1)));
        Button player = new Button("Player POV"), top = new Button("上面"), side = new Button("側面"), free = new Button("自由視点");
        player.setOnAction(e -> playerView());
        top.setOnAction(e -> orbitView(0, -89.9, -46));
        side.setOnAction(e -> orbitView(90, 0, -46));
        free.setOnAction(e -> orbitView(-35, -25, -46));
        HBox buttons = new HBox(8, play, reset, step, new Separator(), player, top, side, free);
        buttons.setAlignment(Pos.CENTER_LEFT);
        timeline.setBlockIncrement(1); timeline.setOnMousePressed(e -> setPlaying(false));
        timeline.valueProperty().addListener((o,a,b) -> { if (!updating) seek(b.doubleValue()); });
        HBox line = new HBox(14, timeline, readout); line.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(timeline, Priority.ALWAYS); readout.setMinWidth(300); readout.setStyle("-fx-text-fill: #d8e7f3;");
        VBox box = new VBox(10, buttons, line); box.setPadding(new Insets(14,22,16,22)); return box;
    }

    private void buildWorld() {
        PhongMaterial grid = new PhongMaterial(Color.web("#263f55"));
        for (int i = -30; i <= 30; i++) {
            Box a = new Box(60,0.025,0.025); a.setTranslateZ(i); a.setMaterial(grid);
            Box b = new Box(0.025,0.025,60); b.setTranslateX(i); b.setMaterial(grid);
            world.getChildren().addAll(a,b);
        }
        Sphere ghast = new Sphere(0.45,16); ghast.setTranslateY(-2);
        ghast.setMaterial(new PhongMaterial(Color.web("#ffad52")));
        Box player = new Box(0.6,1.8,0.6); player.setTranslateY(-2); player.setTranslateZ(24);
        player.setMaterial(new PhongMaterial(Color.web("#68e4a8"))); playerMarker = player;
        world.getChildren().addAll(ghast, player, particles);
    }

    private void syncScore() {
        updating = true;
        durationField.setText(Integer.toString(score.durationTicks()));
        refreshTrackList();
        selectedTrack = Math.max(0, Math.min(selectedTrack, score.tracks().size()-1));
        trackList.getSelectionModel().select(selectedTrack);
        syncSelectedTrackFields();
        updating = false; inputsValid = true;
        message("Score準備完了", false);
    }

    private void refreshTrackList() {
        var labels = new ArrayList<String>();
        for (int i=0;i<score.tracks().size();i++) {
            var t=score.tracks().get(i);
            labels.add(String.format("%02d  %s  [%d..%d]  %s", i+1,t.name(),t.startTick(),t.endTick(),t.pattern().pattern()));
        }
        trackList.getItems().setAll(labels);
    }

    private void syncSelectedTrack() {
        updating = true; syncSelectedTrackFields(); updating = false; inputsValid = true; redraw();
    }

    private void syncSelectedTrackFields() {
        if (score.tracks().isEmpty()) return;
        var t=score.tracks().get(selectedTrack); var p=t.pattern();
        nameField.setText(t.name()); frame.setValue(t.frame()); kind.setValue(p.pattern());
        set("startTick",t.startTick()); set("endTick",t.endTick()); set("forwardSpeed",t.forwardSpeed()); set("phaseDeg",t.phaseDeg());
        set("hue",t.hue()); set("radius",t.radius()); set("bullets",p.bullets()); set("speed",p.speed());
        set("intervalTicks",p.intervalTicks()); set("fanAngleDeg",p.fanAngleDeg());
        set("rotationDegPerSecond",p.rotationDegPerSecond()); set("elevationDeg",p.elevationDeg());
        set("lifetimeTicks",p.lifetimeTicks());
    }

    private void set(String key, Object value) { fields.get(key).setText(String.valueOf(value)); }

    private void applyFields() {
        if (updating || fields.size()!=13 || score.tracks().isEmpty()) return;
        try {
            int duration = Integer.parseInt(durationField.getText().strip());
            int start = integer("startTick"), end = integer("endTick");
            var pattern = new Pattern.Config(kind.getValue(), integer("bullets"), number("speed"), integer("intervalTicks"),
                number("fanAngleDeg"), number("rotationDegPerSecond"), number("elevationDeg"), integer("lifetimeTicks"), end-start);
            var replacement = new Score.Track(nameField.getText().strip(), start, end, pattern, frame.getValue(),
                number("forwardSpeed"), number("phaseDeg"), number("hue"), number("radius"));
            var tracks = new ArrayList<>(score.tracks()); tracks.set(selectedTrack, replacement);
            score = new Score.Config(duration, tracks); tick = Math.min(tick, score.durationTicks());
            inputsValid = true;
            updating = true; refreshTrackList(); trackList.getSelectionModel().select(selectedTrack); updating = false;
            message("Track変更を反映", false); redraw();
        } catch (RuntimeException ex) {
            inputsValid = false; message("入力を確認: " + ex.getMessage(), true);
        }
    }
    private double number(String key) { return Double.parseDouble(fields.get(key).getText().strip()); }
    private int integer(String key) { return Integer.parseInt(fields.get(key).getText().strip()); }

    private void redraw() {
        var bullets = Score.at(score, tick);
        while (pool.size() < bullets.size()) {
            Sphere sphere = new Sphere(0.12,8); PhongMaterial material = new PhongMaterial();
            sphere.setMaterial(material); pool.add(sphere); materials.add(material); particles.getChildren().add(sphere);
        }
        for (int i=0;i<pool.size();i++) {
            Sphere sphere=pool.get(i); sphere.setVisible(i<bullets.size());
            if (i>=bullets.size()) continue;
            var b=bullets.get(i); var track=score.tracks().get(b.trackIndex());
            sphere.setRadius(b.radius());
            sphere.setTranslateX(b.x()); sphere.setTranslateY(-b.y()); sphere.setTranslateZ(b.z());
            double age=Math.max(0,Math.min(1,(tick-b.bornTick())/track.pattern().lifetimeTicks()));
            Color base=Color.hsb(b.hue(),0.78,1.0);
            materials.get(i).setDiffuseColor(base.interpolate(Color.WHITE,0.18*age));
        }
        long active=score.tracks().stream().filter(t -> tick>=t.startTick() && tick<=t.endTick()).count();
        updating=true; timeline.setMax(score.durationTicks()); timeline.setValue(tick); updating=false;
        readout.setText(String.format(java.util.Locale.ROOT,"%.2f秒 / %.0f tick  •  %d弾  •  %d Track",tick/20,tick,bullets.size(),active));
    }

    private void playerView() {
        yaw.setAngle(180); pitch.setAngle(0); camera.setFieldOfView(70);
        camera.setTranslateX(0); camera.setTranslateY(-2); camera.setTranslateZ(24);
        resetRigPan(); playerMarker.setVisible(false);
    }
    private void orbitView(double y,double p,double z) {
        yaw.setAngle(y); pitch.setAngle(p); camera.setFieldOfView(45);
        camera.setTranslateX(0); camera.setTranslateY(0); camera.setTranslateZ(z);
        resetRigPan(); playerMarker.setVisible(true);
    }
    private void resetRigPan() { cameraRig.setTranslateX(0); cameraRig.setTranslateY(0); cameraRig.setTranslateZ(0); }

    private void setPlaying(boolean value) { playing=value; lastNano=0; play.setText(value ? "Ⅱ 停止" : "▶ 再生"); }
    private void seek(double value) { setPlaying(false); tick=value; redraw(); }

    private void chooseFile(boolean save) {
        if (save && !inputsValid) { message("入力を確認してから保存してください", true); return; }
        FileChooser chooser=new FileChooser(); chooser.setTitle(save ? "Score保存" : "Score読込");
        chooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("Score JSON","*.json"));
        chooser.setInitialFileName("grand-danmaku-score.json");
        var file=save ? chooser.showSaveDialog(stage) : chooser.showOpenDialog(stage);
        if (file==null) return;
        try { if (save) save(file.toPath()); else load(file.toPath()); }
        catch (IOException | IllegalArgumentException ex) { message("ファイル処理失敗: "+ex.getMessage(), true); }
    }
    private void save(Path file) throws IOException {
        if (!inputsValid) throw new IllegalArgumentException("invalid track fields");
        Files.writeString(file,ScoreJson.write(score),StandardCharsets.UTF_8); message("保存: "+file.getFileName(),false);
    }
    private void load(Path file) throws IOException {
        if (Files.size(file)>262144) throw new IllegalArgumentException("Score JSON size limit: 256KiB");
        score=ScoreJson.read(Files.readString(file,StandardCharsets.UTF_8)); tick=Math.min(tick,score.durationTicks());
        setPlaying(false); syncScore(); redraw(); message("読込: "+file.getFileName(),false);
    }

    private static Label label(String text,String style) {
        Label label=new Label(text); label.setStyle("-fx-text-fill: #eaf2f8;"+style); return label;
    }
    private void message(String text,boolean error) {
        status.setText(text); status.setStyle("-fx-text-fill: "+(error ? "#b23b35" : "#316c55")+";");
    }

    public static void main(String[] args) { launch(args); }
}
