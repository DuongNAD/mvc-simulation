/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package view;

import dto.DoctorResponseDTO;
import java.util.Map;

public class DoctorView {
    private Map<String, DoctorResponseDTO> doctorMap;
    
    //set de chinh sua thong tin
    public void setDoctorMap(Map<String, DoctorResponseDTO> doctorMap) {
        this.doctorMap = doctorMap;
    }
    
    //Hien thi thong tin
    public void display(){
        // Hiển thị header
        System.out.printf("%-10s%-15s%-20s%-10s\n", "Code", "Name", "Specialization", "Availability");
        // Duyệt qua danh sách và hiển thị từng thông tin
        for(DoctorResponseDTO doctor : doctorMap.values()){
            System.out.println(doctor);
        }
    }
    
}
