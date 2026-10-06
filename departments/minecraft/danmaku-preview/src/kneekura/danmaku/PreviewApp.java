package kneekura.danmaku;

import javafx.animation.AnimationTimer;
import javafx.animation.PauseTransition;
import javafx.application.Application;
import javafx.application.ConditionalFeature;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.input.MouseButton;
import javafx.scene.input.MouseEvent;
import javafx.scene.input.PickResult;
import javafx.scene.*;
import javafx.scene.control.*;
import javafx.scene.image.WritableImage;
import javafx.scene.layout.*;
import javafx.scene.paint.Color;
import javafx.scene.paint.PhongMaterial;
import javafx.scene.shape.Box;
import javafx.scene.shape.Sphere;
import javafx.scene.transform.Rotate;
import javafx.stage.FileChooser;
import javafx.stage.Stage;
import javafx.util.Duration;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;

public final class PreviewApp extends Application {
    private Pattern.Config config = Pattern.defaults();
    private final Group world = new Group(), particles = new Group(), cameraRig = new Group();
    private final ArrayList<Sphere> pool = new ArrayList<>();
    private final ArrayList<PhongMaterial> materials = new ArrayList<>();
    private final LinkedHashMap<String, TextField> fields = new LinkedHashMap<>();
    private final ComboBox<Pattern.Kind> kind = new ComboBox<>();
    private final Label status = new Label(), readout = new Label();
    private final Slider timeline = new Slider(0, 400, 0);
    private final Button play = new Button("▶ 再生");
    private final Rotate yaw = new Rotate(-35, Rotate.Y_AXIS), pitch = new Rotate(-30, Rotate.X_AXIS);
    private final PerspectiveCamera camera = new PerspectiveCamera(true);
    private double tick, dragX, dragY;
    private long lastNano;
    private boolean playing, updating, inputsValid = true;
    private BorderPane root;
    private Stage stage;
    private SubScene viewport;

    @Override public void start(Stage stage) {
        this.stage = stage;
        if (!Platform.isSupported(ConditionalFeature.SCENE3D))
            throw new IllegalStateException("JavaFX SCENE3D is unavailable on this graphics environment");
        buildWorld();
        camera.setNearClip(0.1); camera.setFarClip(1000); camera.setTranslateZ(-42);
        cameraRig.getTransforms().addAll(yaw, pitch); cameraRig.getChildren().add(camera);
        Group sceneRoot = new Group(world, cameraRig, new AmbientLight(Color.WHITE));
        viewport = new SubScene(sceneRoot, 850, 620, true, SceneAntialiasing.BALANCED);
        viewport.setFill(Color.web("#101924")); viewport.setCamera(camera);
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
        viewport.setOnScroll(e -> camera.setTranslateZ(Math.max(-180, Math.min(-8,
            camera.getTranslateZ() + e.getDeltaY() * 0.05))));
        root = new BorderPane(view);
        root.setRight(editor()); root.setTop(header()); root.setBottom(transport());
        root.setStyle("-fx-background-color: #162231; -fx-font-family: 'Yu Gothic UI'; -fx-font-size: 13px;");
        Scene scene = new Scene(root, 1180, 780, true);
        stage.setTitle("KNEEKURA / 弾幕スケッチ"); stage.setScene(scene);
        stage.setMinWidth(950); stage.setMinHeight(680);
        stage.iconifiedProperty().addListener((o, old, minimized) -> { if (minimized) setPlaying(false); });
        syncFields(config); redraw(); stage.show();
        new AnimationTimer() {
            @Override public void handle(long now) {
                if (!playing) { lastNano = 0; return; }
                if (lastNano != 0) {
                    tick = Math.min(config.durationTicks(), tick + (now - lastNano) / 1e9 * 20);
                    redraw();
                    if (tick >= config.durationTicks()) setPlaying(false);
                }
                lastNano = playing ? now : 0;
            }
        }.start();
        List<String> args = getParameters().getRaw();
        if (args.size() == 2 && args.get(0).equals("--smoke")) {
            PauseTransition delay = new PauseTransition(Duration.seconds(1));
            delay.setOnFinished(e -> smoke(Path.of(args.get(1)))); delay.play();
        }
    }

    private Node header() {
        Label title = label("弾幕スケッチ", "-fx-font-size: 23px; -fx-font-weight: bold;");
        Label note = label("JAVA FX 3D  /  下書き → Minecraft水槽で仕上げ", "-fx-text-fill: #96aec5;");
        VBox box = new VBox(4, title, note); box.setPadding(new Insets(18, 22, 14, 22));
        return box;
    }

    private Node editor() {
        VBox pane = new VBox(10); pane.setPadding(new Insets(16)); pane.setPrefWidth(300);
        pane.setStyle("-fx-background-color: #eaf0f5;");
        Label title = new Label("パターンと数値"); title.setStyle("-fx-font-size: 17px; -fx-font-weight: bold;");
        kind.getItems().setAll(Pattern.Kind.values()); kind.setMaxWidth(Double.MAX_VALUE);
        kind.setConverter(new javafx.util.StringConverter<>() {
            @Override public String toString(Pattern.Kind value) {
                return value == null ? "" : switch(value) { case FAN -> "扇状"; case RING -> "全周"; case SPIRAL -> "回転連射"; };
            }
            @Override public Pattern.Kind fromString(String value) { throw new UnsupportedOperationException(); }
        });
        kind.valueProperty().addListener((o, old, value) -> applyFields());
        pane.getChildren().addAll(title, kind);
        GridPane grid = new GridPane(); grid.setHgap(10); grid.setVgap(9);
        String[][] rows = {{"bullets", "弾数 / 1回"}, {"speed", "速度 / block/tick"},
            {"intervalTicks", "発射間隔 / tick"}, {"fanAngleDeg", "扇の角度 / °"},
            {"rotationDegPerSecond", "回転 / °/秒"}, {"elevationDeg", "仰角 / °"},
            {"lifetimeTicks", "寿命 / tick"}, {"durationTicks", "期間 / tick"}};
        for (int i = 0; i < rows.length; i++) {
            TextField field = new TextField(); field.setPrefColumnCount(6);
            fields.put(rows[i][0], field); grid.add(new Label(rows[i][1]), 0, i); grid.add(field, 1, i);
            field.textProperty().addListener((o, old, value) -> applyFields());
        }
        Button save = new Button("JSON保存"), load = new Button("読み込み");
        save.setOnAction(e -> chooseFile(true)); load.setOnAction(e -> chooseFile(false));
        status.setWrapText(true); status.setMinHeight(50);
        Label help = new Label("入力は現在時刻へ即反映\n1 block = 1単位 / 20 tick = 1秒\n同時弾数 ≤ 3,000 / 期間 ≤ 60秒\n\n橙：発射点　緑：プレイヤー目印\n左ドラッグ：視点回転\n右ドラッグ：平行移動\nホイール：拡大・縮小\n\n等速直線の下書きです。\n衝突・重力・damageは実機で確認。");
        help.setWrapText(true); help.setStyle("-fx-text-fill: #526479; -fx-font-size: 12px;");
        pane.getChildren().addAll(grid, new Separator(), new HBox(8, save, load), status, help);
        ScrollPane scroll = new ScrollPane(pane); scroll.setFitToWidth(true); scroll.setPrefWidth(302);
        return scroll;
    }

    private Node transport() {
        play.setOnAction(e -> { if (!playing && tick >= config.durationTicks()) tick = 0; setPlaying(!playing); redraw(); });
        Button reset = new Button("↺ 最初から"), step = new Button("+1 tick");
        reset.setOnAction(e -> seek(0)); step.setOnAction(e -> seek(Math.min(config.durationTicks(), Math.floor(tick) + 1)));
        Button top = new Button("上面"), side = new Button("側面"), free = new Button("自由視点");
        top.setOnAction(e -> view(0, -89.9)); side.setOnAction(e -> view(90, 0)); free.setOnAction(e -> view(-35, -30));
        HBox buttons = new HBox(8, play, reset, step, new Separator(), top, side, free);
        buttons.setAlignment(Pos.CENTER_LEFT);
        timeline.setBlockIncrement(1); timeline.setMajorTickUnit(100);
        timeline.setOnMousePressed(e -> setPlaying(false));
        timeline.valueProperty().addListener((o, old, value) -> { if (!updating) seek(value.doubleValue()); });
        HBox line = new HBox(16, timeline, readout); line.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(timeline, Priority.ALWAYS); readout.setMinWidth(220); readout.setStyle("-fx-text-fill: #cfe0ef;");
        VBox box = new VBox(12, buttons, line); box.setPadding(new Insets(16, 22, 18, 22));
        return box;
    }

    private void buildWorld() {
        PhongMaterial grid = new PhongMaterial(Color.web("#304960"));
        for (int i = -20; i <= 20; i++) {
            Box a = new Box(40, 0.025, 0.025); a.setTranslateZ(i); a.setMaterial(grid);
            Box b = new Box(0.025, 0.025, 40); b.setTranslateX(i); b.setMaterial(grid);
            world.getChildren().addAll(a, b);
        }
        Sphere origin = new Sphere(0.32, 16); origin.setTranslateY(-2);
        origin.setMaterial(new PhongMaterial(Color.web("#ffb95c")));
        Box target = new Box(0.6, 1.8, 0.6); target.setTranslateY(-2); target.setTranslateZ(8);
        target.setMaterial(new PhongMaterial(Color.web("#6fe0ad")));
        world.getChildren().addAll(origin, target, particles);
    }

    private void applyFields() {
        if (updating || fields.size() != 8) return;
        try {
            var next = new Pattern.Config(kind.getValue(), integer("bullets"), number("speed"), integer("intervalTicks"),
                number("fanAngleDeg"), number("rotationDegPerSecond"), number("elevationDeg"), integer("lifetimeTicks"), integer("durationTicks"));
            config = next; tick = Math.min(tick, config.durationTicks());
            inputsValid = true; message("変更を反映しました", false); redraw();
        } catch (IllegalArgumentException ex) { inputsValid = false; message("入力を確認してください: " + ex.getMessage(), true); }
    }
    private double number(String key) { return Double.parseDouble(fields.get(key).getText().strip()); }
    private int integer(String key) { return Integer.parseInt(fields.get(key).getText().strip()); }

    private void syncFields(Pattern.Config next) {
        updating = true;
        kind.setValue(next.pattern());
        String[] values = {"" + next.bullets(), "" + next.speed(), "" + next.intervalTicks(), "" + next.fanAngleDeg(),
            "" + next.rotationDegPerSecond(), "" + next.elevationDeg(), "" + next.lifetimeTicks(), "" + next.durationTicks()};
        int i = 0; for (TextField field : fields.values()) field.setText(values[i++]);
        updating = false; inputsValid = true; config = next; tick = Math.min(tick, next.durationTicks());
        message("準備完了 / 数値を変えると即反映", false);
    }

    private void redraw() {
        var bullets = Pattern.at(config, tick);
        while (pool.size() < bullets.size()) {
            Sphere sphere = new Sphere(0.13, 8); PhongMaterial material = new PhongMaterial();
            sphere.setMaterial(material); pool.add(sphere); materials.add(material); particles.getChildren().add(sphere);
        }
        for (int i = 0; i < pool.size(); i++) {
            Sphere sphere = pool.get(i); sphere.setVisible(i < bullets.size());
            if (i >= bullets.size()) continue;
            var bullet = bullets.get(i);
            sphere.setTranslateX(bullet.x()); sphere.setTranslateY(-bullet.y()); sphere.setTranslateZ(bullet.z());
            double age = (tick - bullet.bornTick()) / config.lifetimeTicks();
            Color base = Color.hsb((bullet.bornTick() / config.intervalTicks() * 137.508 + 200) % 360, 0.65, 1);
            materials.get(i).setDiffuseColor(base.interpolate(Color.TOMATO, age));
        }
        updating = true; timeline.setMax(config.durationTicks()); timeline.setValue(tick); updating = false;
        readout.setText(String.format(java.util.Locale.ROOT, "%.2f秒 / %.0f tick   •   %d弾", tick / 20, tick, bullets.size()));
    }

    private void setPlaying(boolean value) { playing = value; lastNano = 0; play.setText(value ? "Ⅱ 停止" : "▶ 再生"); }
    private void seek(double value) { setPlaying(false); tick = value; redraw(); }
    private void view(double y, double p) {
        yaw.setAngle(y); pitch.setAngle(p); camera.setTranslateZ(-42);
        cameraRig.setTranslateX(0); cameraRig.setTranslateY(0); cameraRig.setTranslateZ(0);
    }
    private static Label label(String text, String style) { Label label = new Label(text); label.setStyle("-fx-text-fill: #eaf2f8;" + style); return label; }
    private void message(String text, boolean error) { status.setText(text); status.setStyle("-fx-text-fill: " + (error ? "#b23b35" : "#316c55") + ";"); }

    private void chooseFile(boolean save) {
        if (save && !inputsValid) { message("入力を確認してから保存してください", true); return; }
        FileChooser chooser = new FileChooser(); chooser.setTitle(save ? "弾幕の下書きを保存" : "弾幕の下書きを読み込み");
        chooser.getExtensionFilters().add(new FileChooser.ExtensionFilter("弾幕JSON", "*.json")); chooser.setInitialFileName("danmaku.json");
        var file = save ? chooser.showSaveDialog(stage) : chooser.showOpenDialog(stage);
        if (file == null) return;
        try { if (save) save(file.toPath()); else load(file.toPath()); }
        catch (IOException | IllegalArgumentException ex) { message("ファイルを処理できません: " + ex.getMessage(), true); }
    }
    private void save(Path file) throws IOException {
        if (!inputsValid) throw new IllegalArgumentException("入力を確認してから保存してください");
        Files.writeString(file, PatternJson.write(config), StandardCharsets.UTF_8);
        message("保存: " + file.getFileName(), false);
    }
    private void load(Path file) throws IOException {
        if (Files.size(file) > 16384) throw new IllegalArgumentException("JSON size limit: 16KiB");
        var next = PatternJson.read(Files.readString(file, StandardCharsets.UTF_8));
        setPlaying(false); syncFields(next); redraw(); message("読み込み: " + file.getFileName(), false);
    }

    private void smoke(Path directory) {
        try {
            Files.createDirectories(directory);
            kind.setValue(Pattern.Kind.SPIRAL); fields.get("bullets").setText("18"); fields.get("elevationDeg").setText("12");
            seek(85); var valid = config;
            fields.get("speed").setText("NaN");
            if (!config.equals(valid) || !status.getText().startsWith("入力")) throw new AssertionError("invalid edit replaced config");
            Path invalidFile = directory.resolve("invalid-input.json");
            try { save(invalidFile); throw new AssertionError("invalid fields must block save"); }
            catch (IllegalArgumentException expected) {
                if (Files.exists(invalidFile) || !status.getText().startsWith("入力")) throw new AssertionError("invalid save side effect");
            }
            fields.get("speed").setText("0.18");
            Path json = directory.resolve("roundtrip.json"); save(json);
            kind.setValue(Pattern.Kind.FAN); load(json);
            if (!config.equals(valid) || Math.abs(tick - 85) > 1e-9) throw new AssertionError("round trip");
            seek(10); seek(85); if (particles.getChildren().stream().filter(Node::isVisible).count() != 144) throw new AssertionError("seek positions");
            setPlaying(true); setPlaying(false); if (lastNano != 0 || playing) throw new AssertionError("pause clock");
            view(0, -89.9); view(90, 0); view(-35, -30);
            for (double[] angles : new double[][] {{-35, -30}, {0, -89.9}, {90, 0}}) {
                view(angles[0], angles[1]);
                viewport.fireEvent(new MouseEvent(MouseEvent.MOUSE_PRESSED, 100, 100, 100, 100,
                    MouseButton.SECONDARY, 1, false, false, false, false, false, false, true,
                    false, false, true, new PickResult(viewport, 100, 100)));
                viewport.fireEvent(new MouseEvent(MouseEvent.MOUSE_DRAGGED, 160, 130, 160, 130,
                    MouseButton.SECONDARY, 1, false, false, false, false, false, false, true,
                    false, false, false, new PickResult(viewport, 160, 130)));
                if (yaw.getAngle() != angles[0] || pitch.getAngle() != angles[1])
                    throw new AssertionError("right drag must pan without rotating");
                var delta = cameraRig.getLocalToParentTransform().inverseDeltaTransform(
                    cameraRig.getTranslateX(), cameraRig.getTranslateY(), cameraRig.getTranslateZ());
                if (!(delta.getX() < 0 && delta.getY() < 0) || Math.abs(delta.getZ()) > 1e-8)
                    throw new AssertionError("right drag must move along the camera screen plane");
                view(angles[0], angles[1]);
                if (cameraRig.getTranslateX() != 0 || cameraRig.getTranslateY() != 0 || cameraRig.getTranslateZ() != 0)
                    throw new AssertionError("view preset must recenter pan");
            }
            view(-35, -30);
            viewport.fireEvent(new MouseEvent(MouseEvent.MOUSE_PRESSED, 100, 100, 100, 100,
                MouseButton.PRIMARY, 1, false, false, false, false, true, false, false,
                false, false, true, new PickResult(viewport, 100, 100)));
            viewport.fireEvent(new MouseEvent(MouseEvent.MOUSE_DRAGGED, 160, 130, 160, 130,
                MouseButton.PRIMARY, 1, false, false, false, false, true, false, false,
                false, false, false, new PickResult(viewport, 160, 130)));
            if (yaw.getAngle() == -35 || pitch.getAngle() == -30 || cameraRig.getTranslateX() != 0)
                throw new AssertionError("left drag must retain orbit behavior");
            view(-35, -30);
            message("SMOKE PASS / 保存・読込・編集・巻き戻し・停止・視点", false);
            root.applyCss(); root.layout();
            WritableImage image = root.snapshot(null, null);
            BufferedImage png = new BufferedImage((int) image.getWidth(), (int) image.getHeight(), BufferedImage.TYPE_INT_ARGB);
            for (int y = 0; y < png.getHeight(); y++) for (int x = 0; x < png.getWidth(); x++)
                png.setRGB(x, y, image.getPixelReader().getArgb(x, y));
            ImageIO.write(png, "png", directory.resolve("preview.png").toFile());
            System.out.println("PASS: JavaFX SCENE3D, edit/seek/pause/views/left-orbit/right-pan/JSON; " + directory);
            Platform.exit();
        } catch (Exception | AssertionError ex) { ex.printStackTrace(); Platform.exit(); System.exit(1); }
    }

    public static void main(String[] args) { launch(args); }
}
