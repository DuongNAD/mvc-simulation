/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package main;

import constants.Message;
import controller.DoctorController;
import dto.DoctorRequestDTO;
import java.util.Scanner;
import utils.Validation;

public class Main {

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        DoctorController controller = new DoctorController();
        while (true) {
            //Hien thi menu
            System.out.println(Message.MENU);
            //Hien thi lua chon
            System.out.print(Message.INPUT_CHOICE);
            try {
                int choice = Validation.getChoice(sc.nextLine(), 1, 5);
                switch (choice) {
                    
                    //add doctor
                    case 1:
                    // tao dto de nhap du lieu
                        DoctorRequestDTO dto = new DoctorRequestDTO();
                        
                        //nhapcode
                        System.out.print(Message.INPUT_CODE);
                        dto.setCode(Validation.getString(sc.nextLine()));
                        
                        System.out.print(Message.INPUT_NAME);
                        dto.setName(Validation.getString(sc.nextLine()));
                        
                        System.out.print(Message.INPUT_SPECIALIZATION);
                        dto.setSpecialization(Validation.getString(sc.nextLine()));
                        
                        System.out.print(Message.INPUT_AVAILABILITY);
                        dto.setAvailability(Validation.getPosititveInteger(sc.nextLine()));

                        controller.addDoctor(dto);
                        System.out.println("Add successfully.");
                        break;
                    case 2:
                        //tao update dto
                        DoctorRequestDTO updateDto = new DoctorRequestDTO();
                         //nhap code
                        System.out.print(Message.INPUT_CODE);
                        String updateCode = Validation.getString(sc.nextLine());
                        updateDto.setCode(updateCode);
                       
                        //nhap name
                        System.out.print(Message.INPUT_NAME);
                        updateDto.setName(Validation.getString(sc.nextLine()));
                        
                        //Nhap specialization
                        System.out.print(Message.INPUT_SPECIALIZATION);
                        updateDto.setSpecialization(Validation.getString(sc.nextLine()));
                        
                        //Nhap avalability
                        System.out.print(Message.INPUT_AVAILABILITY);
                        updateDto.setAvailability(Validation.getPosititveInteger(sc.nextLine()));
                        controller.updateDoctor(updateDto);
                        System.out.println("Update successfully.");
                        break;
                        
                    //xoa doctor
                    case 3:
                        //tao update dto
                        DoctorRequestDTO deleteDto = new DoctorRequestDTO();
                        //xoa code
                        System.out.print(Message.INPUT_CODE);
                        String deleteCode = Validation.getString(sc.nextLine());
                        deleteDto.setCode(deleteCode);
                        
                        controller.deleteDoctor(deleteDto);
                        System.out.println("Delete successfully.");
                        break;   
                     
                    //search doctor
                    case 4:
                        //search
                        System.out.print(Message.INPUT_SEARCH);
                        String input = Validation.getString(sc.nextLine());
                        controller.searchDoctor(input);
                        break;    
                    //Thoat chuong trinh
                    case 5:
                        return;

                }
            } catch (Exception e) {
                System.out.println(e.getMessage());
            }

        }
    }
}
