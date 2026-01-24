package com.nsbm.student.management.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.nsbm.student.management.entity.Student;
import com.nsbm.student.management.service.StudentService;
import java.util.List;

@RestController
@RequestMapping("/api/students")
public class StudentController {

    @Autowired
    private StudentService studentService;

    @GetMapping
    public List<Student> getAllStudents() {
        return studentService.getStudent();
    }

    @PostMapping
    public Student createStudent(@RequestBody Student student) {
        return studentService.insertStudent(student);
    }
}