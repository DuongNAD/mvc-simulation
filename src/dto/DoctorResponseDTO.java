/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package dto;

public class DoctorResponseDTO {
    private String code; 
    private String name; 
    private String specialization;
    private int availability;

    public DoctorResponseDTO() {
    }

    public DoctorResponseDTO(String code, String name, String specialization, int availability) {
        this.code = code;
        this.name = name;
        this.specialization = specialization;
        this.availability = availability;
    }

    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getSpecialization() { return specialization; }
    public void setSpecialization(String specialization) { this.specialization = specialization; }

    public int getAvailability() { return availability; }
    public void setAvailability(int availability) { this.availability = availability; }

    @Override
    public String toString() {
        return String.format("%-10s%-15s%-20s%-10d", code, name, specialization, availability);
    }
}
