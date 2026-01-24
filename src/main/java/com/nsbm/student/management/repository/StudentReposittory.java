package com.nsbm.student.management.repository;

import com.nsbm.student.management.entity.Student;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StudentReposittory extends JpaRepository<Student, Long> {



}

