-- ==========================================================
-- Project Progress Monitoring & Evaluation System Schema
-- ==========================================================
-- Engine: InnoDB
-- Charset: utf8mb4
-- Collation: utf8mb4_unicode_ci
-- ==========================================================

CREATE DATABASE IF NOT EXISTS `project_monitoring_db`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `project_monitoring_db`;

-- --------------------------------------------------------
-- 1. roles
-- --------------------------------------------------------
CREATE TABLE `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `role_name` VARCHAR(50) NOT NULL UNIQUE,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 2. users
-- --------------------------------------------------------
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `first_name` VARCHAR(100) NOT NULL,
    `last_name` VARCHAR(100) NOT NULL,
    `role_id` INT NOT NULL,
    `department` VARCHAR(100),
    `enrollment_number` VARCHAR(50) UNIQUE,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE RESTRICT,
    INDEX `idx_users_role` (`role_id`),
    INDEX `idx_users_department` (`department`),
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 3. academic_terms
-- --------------------------------------------------------
CREATE TABLE `academic_terms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `term_name` VARCHAR(100) NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `is_current` BOOLEAN DEFAULT FALSE,
    `created_by` INT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    CHECK (`end_date` > `start_date`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 4. departments
-- --------------------------------------------------------
CREATE TABLE `departments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `code` VARCHAR(50) NOT NULL UNIQUE,
    `head_of_department_id` INT,
    FOREIGN KEY (`head_of_department_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 5. teams
-- --------------------------------------------------------
CREATE TABLE `teams` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `team_name` VARCHAR(100) NOT NULL,
    `academic_term_id` INT NOT NULL,
    `department_id` INT NOT NULL,
    `guide_id` INT,
    `max_members` INT DEFAULT 4,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`academic_term_id`) REFERENCES `academic_terms`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`guide_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    CHECK (`max_members` > 0)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 6. team_members
-- --------------------------------------------------------
CREATE TABLE `team_members` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `team_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `role_in_team` ENUM('leader', 'member') NOT NULL DEFAULT 'member',
    `joined_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_team_user` (`team_id`, `user_id`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 7. projects
-- --------------------------------------------------------
CREATE TABLE `projects` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `team_id` INT NOT NULL UNIQUE,
    `title` VARCHAR(255) NOT NULL,
    `abstract` TEXT,
    `objectives` TEXT,
    `domain` VARCHAR(100),
    `technology_stack` VARCHAR(255),
    `sdg_alignment` VARCHAR(100) DEFAULT 'SDG 9',
    `status` ENUM('proposed', 'approved', 'in_progress', 'completed', 'archived') NOT NULL DEFAULT 'proposed',
    `approved_by` INT,
    `approved_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`approved_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_projects_status` (`status`),
    INDEX `idx_projects_domain` (`domain`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 8. milestones
-- --------------------------------------------------------
CREATE TABLE `milestones` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `milestone_order` INT NOT NULL,
    `academic_term_id` INT NOT NULL,
    `deadline` DATE,
    `weightage_percent` DECIMAL(5,2) DEFAULT 0.00,
    `is_mandatory` BOOLEAN DEFAULT TRUE,
    `created_by` INT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`academic_term_id`) REFERENCES `academic_terms`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_milestones_term` (`academic_term_id`),
    INDEX `idx_milestones_order` (`milestone_order`),
    CHECK (`weightage_percent` >= 0 AND `weightage_percent` <= 100)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 9. submissions
-- --------------------------------------------------------
CREATE TABLE `submissions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `milestone_id` INT NOT NULL,
    `submitted_by` INT NOT NULL,
    `submission_text` TEXT,
    `document_url` VARCHAR(500),
    `repository_url` VARCHAR(500),
    `status` ENUM('pending', 'submitted', 'under_review', 'revision_required', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    `submitted_at` TIMESTAMP NULL,
    `reviewed_by` INT,
    `reviewed_at` TIMESTAMP NULL,
    `revision_count` INT DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`milestone_id`) REFERENCES `milestones`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`submitted_by`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`reviewed_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    UNIQUE KEY `uk_project_milestone` (`project_id`, `milestone_id`),
    INDEX `idx_submissions_status` (`status`),
    INDEX `idx_submissions_project` (`project_id`),
    INDEX `idx_submissions_milestone` (`milestone_id`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 10. rubric_templates
-- --------------------------------------------------------
CREATE TABLE `rubric_templates` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `academic_term_id` INT NOT NULL,
    `created_by` INT,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`academic_term_id`) REFERENCES `academic_terms`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 11. rubric_criteria
-- --------------------------------------------------------
CREATE TABLE `rubric_criteria` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `rubric_template_id` INT NOT NULL,
    `criterion_name` VARCHAR(255) NOT NULL,
    `max_marks` DECIMAL(5,2) NOT NULL,
    `weightage` DECIMAL(5,2) NOT NULL,
    `description` TEXT,
    `display_order` INT,
    FOREIGN KEY (`rubric_template_id`) REFERENCES `rubric_templates`(`id`) ON DELETE CASCADE,
    INDEX `idx_criteria_rubric` (`rubric_template_id`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 12. evaluation_scores
-- --------------------------------------------------------
CREATE TABLE `evaluation_scores` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `submission_id` INT NOT NULL,
    `rubric_criteria_id` INT NOT NULL,
    `evaluator_id` INT NOT NULL,
    `marks_obtained` DECIMAL(5,2) NOT NULL,
    `remarks` TEXT,
    `evaluated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`submission_id`) REFERENCES `submissions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`rubric_criteria_id`) REFERENCES `rubric_criteria`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`evaluator_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_eval_score` (`submission_id`, `rubric_criteria_id`, `evaluator_id`),
    INDEX `idx_eval_submission` (`submission_id`),
    INDEX `idx_eval_evaluator` (`evaluator_id`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 13. feedback_logs
-- --------------------------------------------------------
CREATE TABLE `feedback_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `submission_id` INT NOT NULL,
    `author_id` INT NOT NULL,
    `feedback_type` ENUM('comment', 'revision_request', 'approval', 'rejection', 'meeting_note') NOT NULL,
    `content` TEXT NOT NULL,
    `is_private` BOOLEAN DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`submission_id`) REFERENCES `submissions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`author_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_feedback_submission` (`submission_id`),
    INDEX `idx_feedback_author` (`author_id`),
    INDEX `idx_feedback_created` (`created_at`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 14. meeting_logs
-- --------------------------------------------------------
CREATE TABLE `meeting_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `team_id` INT NOT NULL,
    `scheduled_by` INT NOT NULL,
    `meeting_date` DATE NOT NULL,
    `duration_minutes` INT,
    `agenda` TEXT,
    `minutes` TEXT,
    `attendees_count` INT,
    `status` ENUM('scheduled', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`scheduled_by`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 15. notifications
-- --------------------------------------------------------
CREATE TABLE `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `message` TEXT NOT NULL,
    `notification_type` ENUM('submission', 'feedback', 'deadline', 'approval', 'system') NOT NULL,
    `is_read` BOOLEAN DEFAULT FALSE,
    `related_entity_type` VARCHAR(50),
    `related_entity_id` INT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_notifications_user` (`user_id`, `is_read`, `created_at`)
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 16. activity_log
-- --------------------------------------------------------
CREATE TABLE `activity_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `action` VARCHAR(100) NOT NULL,
    `entity_type` VARCHAR(50),
    `entity_id` INT,
    `details` TEXT,
    `ip_address` VARCHAR(45),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_activity_log_user` (`user_id`),
    INDEX `idx_activity_log_entity` (`entity_type`),
    INDEX `idx_activity_log_created` (`created_at`)
) ENGINE=InnoDB;
