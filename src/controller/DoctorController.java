/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package controller;

import constants.Message;
import dto.DoctorRequestDTO;
import dto.DoctorResponseDTO;
import java.util.Map;
import repository.DoctorRepository;
import view.DoctorView;

public class DoctorController {
    private DoctorRepository doctorRepository;
    private DoctorView doctorView;

    //constructor co chua view va repository
    public DoctorController() {
        doctorRepository = new DoctorRepository();
        doctorView = new DoctorView();
    }
    
    //Fuction 1: Add Doctor
    public void addDoctor(DoctorRequestDTO requestDTO)throws Exception{
        //Kiem tra code co bi trung hay k
        if(doctorRepository.isDuplicate(requestDTO.getCode())){
            throw new Exception(Message.DUPLICATE);
        }
        doctorRepository.addDoctor(requestDTO);
    }
    
    //Fuction 2: Update doctor
    public void updateDoctor(DoctorRequestDTO requestDTO)throws Exception{
        //Kiem tra xem co ton tai hay k
        if(!doctorRepository.isExistDoctor(requestDTO.getCode())){
            throw new Exception(Message.NO_DOCTOR_AVAILABLE);
        }
        doctorRepository.updateDoctor(requestDTO);
    }
    
    //Fuction 3: delete Doctor
    public void deleteDoctor(DoctorRequestDTO requestDTO)throws Exception{
        //Kiem tra xem co ton tai hay k
        if(!doctorRepository.isExistDoctor(requestDTO.getCode())){
            throw new Exception(Message.NO_DOCTOR_AVAILABLE);
        }
        doctorRepository.deleteDoctor(requestDTO);
    }
    
    //Function 4: Search doctor
    public void searchDoctor(String input)throws Exception{

        //Kiem tra database co du lieu truoc khi search
        if(doctorRepository.isEmpty()){
            throw new Exception(Message.DATABASE_EMPTY);
        }
        //neu k thay ket qua 
        Map<String, DoctorResponseDTO> result = doctorRepository.searchDoctor(input);
        if(result == null || result.isEmpty()){
            throw new Exception(Message.NO_DOCTOR_AVAILABLE);
        }
        //Truyen du lieu sang view 
        doctorView.setDoctorMap(result);
        doctorView.display();
    }
}
