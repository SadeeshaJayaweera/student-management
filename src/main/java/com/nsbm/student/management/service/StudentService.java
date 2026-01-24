package com.nsbm.student.management.service;


import com.nsbm.student.management.entity.Student;
import com.nsbm.student.management.repository.StudentReposittory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service

public class StudentService {

    @Autowired
    private StudentReposittory studentReposittory;

    public List<Student> getStudent(){
        return studentReposittory.findAll();
    }


    public Student insertStudent(Student student) {
        return studentReposittory.save(student);
    }
}
