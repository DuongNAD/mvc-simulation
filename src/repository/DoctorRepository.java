/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package repository;

import dto.DoctorRequestDTO;
import dto.DoctorResponseDTO;
import java.util.HashMap;
import java.util.Map;
import model.Doctor;

public class DoctorRepository {
     //  Danh sách bác sỹ
    private Map<String, Doctor> doctorMap = new HashMap<>();

    //gia lap database bang Map
    public DoctorRepository() {

    }
    
    //add doctor
    public boolean addDoctor(DoctorRequestDTO requestDTO){
        Doctor doctor = new Doctor(
                requestDTO.getCode(),
                requestDTO.getName(),
                requestDTO.getSpecialization(),
                requestDTO.getAvailability()
        );
        doctorMap.put(doctor.getCode(), doctor);
        return true;
    }
    
    //update doctor
    public boolean updateDoctor(DoctorRequestDTO requestDTO){
        //Lay doctor tu database
        Doctor doctor = doctorMap.get(requestDTO.getCode());
        //Cap nhat thong tin
        doctor.setName(requestDTO.getName());
        doctor.setSpecialization(requestDTO.getSpecialization());
        doctor.setAvailability(requestDTO.getAvailability());
        return true;
    }
    
    //delete doctor
    public boolean deleteDoctor(DoctorRequestDTO requestDTO){
        //xoa doctor theo code
        doctorMap.remove(requestDTO.getCode());
        return true;
    }
    
    //search doctor
    public Map<String, DoctorResponseDTO> searchDoctor(String input){
    
        Map<String, DoctorResponseDTO> result = new HashMap<>();
    
        //duyet qua tat ca doctor
        for(Doctor doctor : doctorMap.values()){
            //xem co chua tu khoa hay k
         if(doctor.getCode().contains(input)
                 || doctor.getName().contains(input)
                 || doctor.getSpecialization().contains(input)){
             //chuyen sang response dto
             result.put(doctor.getCode(), new DoctorResponseDTO(
                     doctor.getCode(),
                     doctor.getName(),
                     doctor.getSpecialization(),
                     doctor.getAvailability()
             ));
         }   
        }
        return result;
    }
    
    //ktra xem co ton tai doctor hay k
    public boolean isExistDoctor(String code){
        return doctorMap.containsKey(code);
    }
    
    //ktra xem co trung code k
    public boolean isDuplicate(String code){
        return doctorMap.containsKey(code);
    }
    
    //ktra xem co rong k
    public boolean isEmpty(){
        return doctorMap.isEmpty();
    }
}
