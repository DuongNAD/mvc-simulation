package main;

import constants.Message;
import controller.StudentController;
import dto.StudentRequestDTO;
import repository.StudentRepository;
import service.StudentService;
import view.StudentView;
import java.util.Scanner;
import utils.Validation;

public class Main {

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        StudentRepository repository = new StudentRepository();
        StudentService service = new StudentService(repository);
        StudentView view = new StudentView();
        StudentController controller = new StudentController(service, view);

        while (true) {
            System.out.println(Message.MENU);
            System.out.print(Message.INPUT_CHOICE);
            try {
                int choice = Validation.getChoice(sc.nextLine(), 1, 4);
                switch (choice) {
                    case 1:
                        System.out.print(Message.INPUT_NAME);
                        String name = Validation.getString(sc.nextLine());
                        StudentRequestDTO requestDTO = new StudentRequestDTO(name);
                        controller.addStudent(requestDTO);
                        break;
                    case 2:
                        System.out.print(Message.INPUT_ID);
                        int id = Validation.getPosititveInteger(sc.nextLine());
                        controller.deleteStudent(id);
                        break;
                    case 3:
                        System.out.print(Message.INPUT_SEARCH);
                        String query = Validation.getString(sc.nextLine());
                        controller.searchStudent(query);
                        break;
                    case 4:
                        return;
                }
            } catch (Exception e) {
                System.out.println(e.getMessage());
            }
        }
    }
}
