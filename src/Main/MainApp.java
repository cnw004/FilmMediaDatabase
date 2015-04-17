/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Main;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.scene.layout.AnchorPane;
import javafx.stage.Stage;

/**
 *
 * @author Zhengri Fan
 */
public class MainApp extends Application {

    private Stage primaryStage;
    private AnchorPane root;

    @Override
    public void start(Stage primaryStage) throws MalformedURLException, IOException {
//        Button btn = new Button();
//        btn.setText("Say 'Hello World'");
//        btn.setOnAction(new EventHandler<ActionEvent>() {
//
//            @Override
//            public void handle(ActionEvent event) {
//                System.out.println("Hello World!");
//            }
//        });
//
//        StackPane root = new StackPane();
//        root.getChildren().add(btn);
//
//        Scene scene = new Scene(root, 300, 250);
//
//        primaryStage.setTitle("Hello World!");
//        primaryStage.setScene(scene);
//        primaryStage.show();
        this.primaryStage = primaryStage;
        this.primaryStage.setTitle("Texas Hold'em");

        FXMLLoader loader = new FXMLLoader();
        //++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        //For the program to run, please ues abslute path here!!!!
        //++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        File xmlFile = new File("./src/view/gameView.fxml");
        loader.setLocation(xmlFile.toURI().toURL());
        root = (AnchorPane) loader.load();

        Scene scene = new Scene(root);
        this.primaryStage.setScene(scene);
        this.primaryStage.show();

    }

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        launch(args);
    }

}
