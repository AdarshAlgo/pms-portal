USE `project_monitoring_db`;

-- --------------------------------------------------------
-- 1. Roles
-- --------------------------------------------------------
INSERT INTO `roles` (`id`, `role_name`, `description`) VALUES
(1, 'admin', 'System Administrator with full access'),
(2, 'faculty', 'Faculty member who guides and evaluates projects'),
(3, 'student', 'Student enrolled in capstone projects');

-- --------------------------------------------------------
-- 2. Departments
-- --------------------------------------------------------
INSERT INTO `departments` (`id`, `name`, `code`) VALUES
(1, 'Computer Science', 'CS'),
(2, 'Information Technology', 'IT'),
(3, 'Electronics', 'EC');

-- --------------------------------------------------------
-- 3. Users (Password is 'password123' for all: $2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi)
-- --------------------------------------------------------
INSERT INTO `users` (`id`, `email`, `password_hash`, `first_name`, `last_name`, `role_id`, `department`, `enrollment_number`) VALUES
(1, 'admin@university.edu', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'System', 'Admin', 1, 'Administration', NULL),
(2, 'dr.smith@university.edu', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'John', 'Smith', 2, 'Computer Science', NULL),
(3, 'dr.jones@university.edu', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Sarah', 'Jones', 2, 'Information Technology', NULL),
(4, 'student1@university.edu', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Alice', 'Williams', 3, 'Computer Science', 'CS2020001'),
(5, 'student2@university.edu', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Bob', 'Brown', 3, 'Computer Science', 'CS2020002');

-- Update department heads
UPDATE `departments` SET `head_of_department_id` = 2 WHERE `id` = 1;

-- --------------------------------------------------------
-- 4. Academic Terms
-- --------------------------------------------------------
INSERT INTO `academic_terms` (`id`, `term_name`, `start_date`, `end_date`, `is_current`, `created_by`) VALUES
(1, 'Fall 2024', '2024-08-01', '2024-12-15', TRUE, 1);

-- --------------------------------------------------------
-- 5. Teams
-- --------------------------------------------------------
INSERT INTO `teams` (`id`, `team_name`, `academic_term_id`, `department_id`, `guide_id`, `max_members`) VALUES
(1, 'Tech Innovators', 1, 1, 2, 4);

-- --------------------------------------------------------
-- 6. Team Members
-- --------------------------------------------------------
INSERT INTO `team_members` (`team_id`, `user_id`, `role_in_team`) VALUES
(1, 4, 'leader'),
(1, 5, 'member');

-- --------------------------------------------------------
-- 7. Projects
-- --------------------------------------------------------
INSERT INTO `projects` (`id`, `team_id`, `title`, `abstract`, `objectives`, `domain`, `technology_stack`, `sdg_alignment`, `status`, `approved_by`, `approved_at`) VALUES
(1, 1, 'AI-Based Crop Disease Detection', 'A system to identify crop diseases from leaf images.', '1. Develop an image classification model. 2. Build a web application for farmers.', 'Artificial Intelligence', 'Python, TensorFlow, React, Node.js', 'SDG 9', 'approved', 2, '2024-08-10 10:00:00');

-- --------------------------------------------------------
-- 8. Milestones
-- --------------------------------------------------------
INSERT INTO `milestones` (`id`, `title`, `description`, `milestone_order`, `academic_term_id`, `deadline`, `weightage_percent`, `is_mandatory`, `created_by`) VALUES
(1, 'Synopsis', 'Project proposal and feasibility study', 1, 1, '2024-09-01', 10.00, TRUE, 1),
(2, 'Literature Review', 'Analysis of existing systems and literature', 2, 1, '2024-09-30', 20.00, TRUE, 1),
(3, 'Implementation', 'Core development phase', 3, 1, '2024-11-15', 40.00, TRUE, 1),
(4, 'Final Presentation', 'Final evaluation and demo', 4, 1, '2024-12-10', 30.00, TRUE, 1);

-- --------------------------------------------------------
-- 9. Submissions
-- --------------------------------------------------------
INSERT INTO `submissions` (`id`, `project_id`, `milestone_id`, `submitted_by`, `submission_text`, `document_url`, `repository_url`, `status`, `submitted_at`, `reviewed_by`, `reviewed_at`) VALUES
(1, 1, 1, 4, 'Please find attached our project synopsis.', 'https://storage.university.edu/docs/synopsis_team1.pdf', NULL, 'approved', '2024-08-25 10:00:00', 2, '2024-08-26 14:30:00'),
(2, 1, 2, 4, 'Literature review submitted.', 'https://storage.university.edu/docs/lit_review_team1.pdf', NULL, 'under_review', '2024-09-28 09:15:00', NULL, NULL);

-- --------------------------------------------------------
-- 10. Rubric Templates
-- --------------------------------------------------------
INSERT INTO `rubric_templates` (`id`, `name`, `description`, `academic_term_id`, `created_by`, `is_active`) VALUES
(1, 'Standard Project Evaluation Rubric', 'Default rubric for capstone projects', 1, 1, TRUE);

-- --------------------------------------------------------
-- 11. Rubric Criteria
-- --------------------------------------------------------
INSERT INTO `rubric_criteria` (`id`, `rubric_template_id`, `criterion_name`, `max_marks`, `weightage`, `description`, `display_order`) VALUES
(1, 1, 'Innovation & Originality', 10.00, 25.00, 'Novelty of the solution proposed.', 1),
(2, 1, 'Technical Implementation', 10.00, 40.00, 'Quality of code and technical design.', 2),
(3, 1, 'Documentation', 10.00, 20.00, 'Clarity and completeness of project report.', 3),
(4, 1, 'Presentation Skills', 10.00, 15.00, 'Ability to communicate ideas effectively.', 4);

-- --------------------------------------------------------
-- 12. Feedback Logs
-- --------------------------------------------------------
INSERT INTO `feedback_logs` (`submission_id`, `author_id`, `feedback_type`, `content`, `is_private`) VALUES
(1, 2, 'approval', 'Good proposal. Proceed with the literature review.', FALSE),
(1, 3, 'comment', 'Looks promising, might need better dataset sources.', TRUE);

-- --------------------------------------------------------
-- 13. Meeting Logs
-- --------------------------------------------------------
INSERT INTO `meeting_logs` (`team_id`, `scheduled_by`, `meeting_date`, `duration_minutes`, `agenda`, `minutes`, `attendees_count`, `status`) VALUES
(1, 2, '2024-08-20', 30, 'Initial setup and topic discussion', 'Discussed 3 potential topics. Selected AI crop detection.', 3, 'completed');
