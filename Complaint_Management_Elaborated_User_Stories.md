Smart Public Complaint Management System - Elaborated User Stories
Smart Public Complaint Management System
Elaborated User Stories
Features: User Management, Complaint Registration & Classification, Priority Assessment & Assignment, Complaint Verification & Resolution, Notifications & Dashboards, Reports & Statistics
Document Overview
This document elaborates the requirements from the Complaint Management System SRS into implementation-ready user stories. Each story includes the business context, functional expectations, key fields, acceptance criteria, business rules, and expected outcome.

# Feature: User Management
## 1. User Registration & Login
User Story: As a Citizen or staff member, I want to register and log in securely so that I can access the functions relevant to my role.
Preconditions
User has a valid email or phone number for registration.
The system is available and accessible.
Role master data (Citizen, Ground-Level Employee, Supervisor, Department Admin, System Admin) is configured.
Key Fields / Information
Acceptance Criteria
Given I am a new user, when I register with valid details, then my account should be created with the appropriate role.
Given I enter valid login credentials, when I log in, then I should be redirected to my role-specific dashboard.
Given I enter incorrect credentials, when I attempt to log in, then the system should show an error and not grant access.
Given my account role is Citizen, when I log in, then I should not see staff-only functions.
Business Rules
Outcome
Users can securely access the system through functions appropriate to their role.
## 2. Role & Permission Management
User Story: As a System Admin, I want to manage roles and permissions so that access to system functions and data is properly controlled.
Preconditions
System Admin is logged in.
Role hierarchy and department structure are defined.
User accounts requiring role changes exist in the system.
Key Fields / Information
Acceptance Criteria
Given I am logged in as System Admin, when I assign a role to a user, then the user should immediately receive the associated permissions.
Given a user attempts to view another department's data through a non-admin role, then access should be denied.
Given I revoke a permission, then the user should lose access to the related function immediately.
Given a role change is made, then it should be recorded in the audit log.
Business Rules
Outcome
Access to system functions and data is properly governed according to each user's role.
# Feature: Complaint Registration & Classification
## 3. Complaint Submission
User Story: As a Citizen, I want to submit a complaint with photos, description, and location so that public issues can be reported and resolved.
Preconditions
Citizen is logged in.
Citizen has internet access and, where required, location services enabled.
Complaint type/category master data is available.
Key Fields / Information
Acceptance Criteria
Given I am a logged-in citizen, when I fill in complaint type, description, and location, then I should be able to submit the complaint.
Given I upload a photo/video, then it should be attached to the complaint.
Given I submit a complaint, then it should receive a unique Complaint ID and status Submitted.
Given required fields are missing, when I try to submit, then the system should show a validation message.
Business Rules
Outcome
A new complaint is registered in the system and made available for classification and processing.
## 4. AI-Based Complaint Classification
User Story: As the System, I want to automatically classify submitted complaints so that they are routed and prioritized correctly with minimal manual effort.
Preconditions
Complaint has been submitted with a description and/or photo.
AI/image-processing service is available.
Complaint category master data is configured.
Key Fields / Information
Acceptance Criteria
Given a complaint is submitted, when AI classification runs, then the complaint should be tagged with a category and severity indicator.
Given the AI confidence score is low, then the complaint should be flagged for manual verification.
Given an employee overrides the AI classification, then the corrected category should be saved and used going forward.
Given classification is complete, then the complaint should proceed to priority assessment.
Business Rules
Outcome
Complaints are consistently categorized, enabling accurate routing and prioritization.
# Feature: Priority Assessment & Assignment
## 5. AI-Based Priority Assessment
User Story: As the System, I want to calculate a priority score for each complaint so that dangerous or high-impact complaints are handled first.
Preconditions
Complaint has been classified.
Location and proximity data (schools, hospitals, high-traffic areas) is available.
Priority scoring rules/weights are configured.
Key Fields / Information
Acceptance Criteria
Given a complaint is classified, when priority assessment runs, then a priority score should be calculated and a category assigned.
Given a complaint is near a school or hospital, then its priority score should increase accordingly.
Given the priority score exceeds the high-priority threshold, then the complaint should be flagged High Priority.
Given priority is assigned, then it should be visible on the department dashboard.
Business Rules
Outcome
High-impact and dangerous complaints are identified and handled ahead of lower-impact ones.
## 6. Duplicate Complaint Detection
User Story: As the System, I want to detect duplicate complaints so that multiple citizens reporting the same issue do not create separate cases.
Preconditions
A new complaint has been submitted and classified.
Existing complaints with location and type data are available for comparison.
Key Fields / Information
Acceptance Criteria
Given a new complaint matches an existing nearby complaint of the same type, then it should be linked to the main complaint instead of creating a new case.
Given a complaint is merged, then the reporter count on the main complaint should increase.
Given no matching complaint is found, then the new complaint should proceed as an independent case.
Given a citizen tracks a merged complaint, then they should see the status of the main complaint.
Business Rules
Outcome
Duplicate reports are consolidated, avoiding redundant cases while preserving citizen reporting counts.
## 7. Location-Based Department Assignment
User Story: As the System, I want to assign complaints to the correct department and employee based on location so that complaints reach the right authority automatically.
Preconditions
Complaint has been classified and prioritized.
Location-to-department/municipality mapping is configured.
Employees are available within the responsible department.
Key Fields / Information
Acceptance Criteria
Given a complaint's location and type are known, when assignment runs, then the correct department should be identified automatically.
Given a department is identified, then the department should be notified of the new complaint.
Given a supervisor reviews unassigned complaints, then they should be able to assign it to a specific employee.
Given assignment is complete, then the complaint status should update accordingly.
Business Rules
Outcome
Complaints are automatically routed to the correct department and employee for action.
# Feature: Complaint Verification & Resolution
## 8. Complaint Verification
User Story: As a Ground-Level Employee, I want to verify a reported complaint so that only genuine issues proceed to resolution.
Preconditions
Complaint has been assigned to the employee's department.
Employee is logged in and has verification permission.
Complaint status is Assigned or Under Verification.
Key Fields / Information
Acceptance Criteria
Given a complaint is assigned to me, when I open it, then I should see full complaint details and location.
Given I inspect the reported issue, when I mark it Verified, then the complaint status should move to Verified.
Given the complaint is found invalid, when I mark it Invalid with remarks, then the complaint should be closed as invalid.
Given I submit a verification decision, then remarks should be mandatory.
Business Rules
Outcome
Only genuine complaints proceed to assignment and resolution, reducing wasted effort.
## 9. Complaint Resolution
User Story: As the assigned Employee, I want to update progress and mark a complaint as resolved with proof so that resolution is properly tracked and confirmed.
Preconditions
Complaint has been verified and assigned to the employee.
Employee is logged in and has resolution permission.
Complaint status is Verified or In Progress.
Key Fields / Information
Acceptance Criteria
Given a complaint is assigned to me, when I update progress, then the citizen should see the latest status.
Given I complete the work, when I mark the complaint Resolved, then resolution proof should be mandatory.
Given I set an expected completion date, then it should be visible to the citizen and supervisor.
Given the deadline is missed, then the complaint should be flagged as overdue for the supervisor.
Business Rules
Outcome
Complaints are resolved with verifiable proof, and progress is transparent to citizens and supervisors.
## 10. Complaint Tracking
User Story: As a Citizen, I want to track my complaint using the Complaint ID so that I stay informed without contacting the department directly.
Preconditions
Citizen has a valid Complaint ID.
Complaint exists in the system.
Key Fields / Information
Acceptance Criteria
Given I enter a valid Complaint ID, when I search, then I should see the complaint's current status and history.
Given the complaint has been merged with another, then I should see the status of the main complaint.
Given the complaint is resolved, then I should see resolution details and proof.
Given I enter an invalid Complaint ID, then the system should show a not-found message.
Business Rules
Outcome
Citizens have full visibility into the progress of their complaints.
# Feature: Notifications & Dashboards
## 11. Notifications
User Story: As the System, I want to notify citizens and departments at key stages so that all parties stay informed without manual follow-up.
Preconditions
Complaint status changes have occurred.
Citizen/department contact details (email, SMS, in-app) are available.
Notification service is configured.
Key Fields / Information
Acceptance Criteria
Given a complaint is submitted, then the citizen should receive a confirmation notification.
Given a complaint status changes, then the citizen should be notified of the update.
Given a complaint is assigned to a department, then that department should be notified.
Given a deadline is approaching or changed, then the citizen should receive an alert.
Business Rules
Outcome
Citizens and departments remain informed throughout the complaint lifecycle.
## 12. Citizen Dashboard
User Story: As a Citizen, I want a personal dashboard so that I can easily manage and monitor my complaints.
Preconditions
Citizen is logged in.
Citizen has submitted at least one complaint (for complaint-related widgets).
Key Fields / Information
Acceptance Criteria
Given I log in as a citizen, when I open my dashboard, then I should see my complaints grouped by status.
Given I enable location sharing, then I should see complaints reported near me.
Given I select a complaint, then I should see its full details.
Given I have new notifications, then they should be visible on my dashboard.
Business Rules
Outcome
Citizens have a centralized view of their complaint activity and relevant local issues.
## 13. Department Dashboard
User Story: As a Supervisor or Department Admin, I want a department dashboard so that I can monitor workload, priorities, and team performance.
Preconditions
Supervisor/Department Admin is logged in.
Complaints have been assigned to the department.
Key Fields / Information
Acceptance Criteria
Given I log in as a Supervisor, when I open the department dashboard, then I should see complaint counts by status and priority.
Given I filter by category or location, then the dashboard should update accordingly.
Given a complaint is overdue, then it should be highlighted for follow-up.
Given I review employee performance, then I should see complaints resolved per employee.
Business Rules
Outcome
Department staff can monitor workload, priorities, and team performance in one place.
## 14. Admin Dashboard
User Story: As a System Admin, I want a central admin dashboard so that I can manage users, departments, and monitor the system as a whole.
Preconditions
System Admin is logged in.
User, department, and role data exist in the system.
Key Fields / Information
Acceptance Criteria
Given I am logged in as System Admin, when I open the admin dashboard, then I should see system-wide complaint and user statistics.
Given I create a new department, then it should become available for complaint assignment.
Given I manage user roles, then the affected users should receive the corresponding access changes.
Given I monitor all departments, then I should see performance across the entire system.
Business Rules
Outcome
The System Admin has full administrative oversight and control across the platform.
# Feature: Reports & Statistics
## 15. Reports & Statistics
User Story: As a Department Admin or System Admin, I want to generate reports and statistics so that I can evaluate performance and plan improvements.
Preconditions
Department Admin/System Admin is logged in and has report access.
Complaint data exists for the selected reporting period.
Key Fields / Information
Acceptance Criteria
Given I am logged in with report access, when I open the reports section, then I should see complaint statistics for the selected period.
Given I apply filters (date, category, location, department), then the report should update accordingly.
Given I export a report, then the system should generate it in Excel or PDF format.
Given I view average resolution time, then it should reflect only resolved/closed complaints.
Business Rules
Outcome
Administrators and leadership gain data-driven insight into complaint trends and department performance.

# Summary of User Stories
# Recommended MVP Scope
Citizen registration, login, and complaint submission with photo & location
AI-assisted (or manual fallback) complaint classification
Location-based department assignment
Complaint verification and resolution workflow
Complaint tracking by Complaint ID
Core notifications (submission, status change, resolution)
Basic department dashboard
Basic admin user, role, and department management

## Tables

| Feature | User Stories Covered |
| --- | --- |
| User Management | User registration & login, role and permission management |
| Complaint Registration & Classification | Complaint submission, AI-based complaint classification |
| Priority Assessment & Assignment | AI-based priority assessment, duplicate complaint detection, location-based department assignment |
| Complaint Verification & Resolution | Complaint verification, complaint resolution, complaint tracking |
| Notifications & Dashboards | Notifications, citizen dashboard, department dashboard, admin dashboard |
| Reports & Statistics | Complaint and performance reports & statistics |

| Item | Details |
| --- | --- |
| Feature | User Management |
| Primary Actor | Citizen / All Users |
| Description | The system should allow citizens and government staff to create accounts and log in securely with role-based access, so each user type reaches only the functions relevant to their role (Citizen, Ground-Level Employee, Supervisor, Department Admin, System Admin). |

| Field / Information | Purpose |
| --- | --- |
| Full Name | Identifies the registering user |
| Email / Phone | Login credential and contact detail |
| Password | Secure authentication credential |
| Role | Determines access level and permissions |
| Department (if applicable) | Links staff accounts to their department |
| Account Status | Active, inactive, or pending verification |

| Rule | Description |
| --- | --- |
| BR-001 | Email/phone used for registration must be unique. |
| BR-002 | Passwords must be stored securely (hashed) and never displayed in plain text. |
| BR-003 | Each user must be assigned exactly one primary role at registration. |
| BR-004 | Staff accounts (employee, supervisor, department admin) require department assignment. |
| BR-005 | Login activity should be captured for security auditing. |

| Item | Details |
| --- | --- |
| Feature | User Management |
| Primary Actor | System Admin |
| Description | The System Admin should be able to create, modify, and manage user roles and permissions so that access to system functions and data is properly governed across the role hierarchy: System Admin → Department Admin → Supervisor → Ground-Level Employee. |

| Field / Information | Purpose |
| --- | --- |
| User | Account being assigned or updated |
| Role | System Admin, Department Admin, Supervisor, Ground-Level Employee, Citizen |
| Department | Department the role applies to |
| Permission Set | Specific functions/data the role can access |
| Modified By / On | Audit information for the change |

| Rule | Description |
| --- | --- |
| BR-001 | Only the System Admin can create or modify system-wide roles and permissions. |
| BR-002 | Department A must not access Department B's complaints or data. |
| BR-003 | A verifier role should not automatically include administrative permissions. |
| BR-004 | Role and permission changes must be captured in the audit log. |
| BR-005 | Deactivated accounts should immediately lose all access. |

| Item | Details |
| --- | --- |
| Feature | Complaint Registration & Classification |
| Primary Actor | Citizen / User |
| Description | Citizens should be able to submit complaints about public infrastructure and service issues with a description, photo/video, and location, so the issue can be tracked and resolved by the responsible department. |

| Field / Information | Purpose |
| --- | --- |
| Complaint Type | Category such as pothole, drainage, garbage, streetlight, etc. |
| Description | Detailed explanation of the issue |
| Photo / Video | Visual evidence of the issue |
| Location | Pinned or tagged location of the issue |
| Inconvenience Details | Impact caused by the issue |
| Expected Solution | Citizen's suggested resolution |
| Date & Time | Timestamp of submission |

| Rule | Description |
| --- | --- |
| BR-001 | Complaint type, description, and location are mandatory fields. |
| BR-002 | Each complaint must be assigned a unique Complaint ID upon submission. |
| BR-003 | Newly submitted complaints should default to status Submitted. |
| BR-004 | Complaint submission should be captured in the audit log. |
| BR-005 | Photo/video attachments should be optional unless required by the complaint type. |

| Item | Details |
| --- | --- |
| Feature | Complaint Registration & Classification |
| Primary Actor | System (AI Classification Engine) |
| Description | The system should automatically classify submitted complaints into predefined categories using AI/image analysis, assisting in identifying the type and severity of each complaint. |

| Field / Information | Purpose |
| --- | --- |
| Complaint ID | Complaint being classified |
| Detected Category | Pothole, drainage, garbage, streetlight, road damage, water supply, sanitation, other |
| Confidence Score | AI's confidence in the classification |
| Severity Indicator | AI-assessed severity of the issue |
| Manual Override | Option for human verification/correction |

| Rule | Description |
| --- | --- |
| BR-001 | AI classification may not always be 100% accurate and may require human verification. |
| BR-002 | Complaints below a configured confidence threshold must be routed for manual review. |
| BR-003 | Manual overrides must be captured in the complaint history. |
| BR-004 | Classification results should be stored with the complaint record. |
| BR-005 | Classification categories should be configurable by the System Admin. |

| Item | Details |
| --- | --- |
| Feature | Priority Assessment & Assignment |
| Primary Actor | System (AI Priority Engine) |
| Description | The system should calculate a priority score for each complaint based on factors such as high-traffic area, proximity to schools or hospitals, and severity of damage, so high-impact complaints are handled first. |

| Field / Information | Purpose |
| --- | --- |
| Complaint ID | Complaint being scored |
| Location Factors | High-traffic area, public area, school nearby, hospital nearby |
| Severity Score | Based on AI/image assessment |
| Total Priority Score | Aggregated score across all factors |
| Priority Category | High, Medium, or Low |

| Rule | Description |
| --- | --- |
| BR-001 | Priority score should be calculated from configurable weighted factors (high traffic area, school nearby, hospital nearby, severity). |
| BR-002 | Complaints should be categorized as High, Medium, or Low priority based on the final score. |
| BR-003 | Priority scoring logic should be maintainable by the System Admin. |
| BR-004 | Priority recalculation should be triggered if location or classification changes. |
| BR-005 | Priority score and category must be stored with the complaint record. |

| Item | Details |
| --- | --- |
| Feature | Priority Assessment & Assignment |
| Primary Actor | System (Duplicate Detection Engine) |
| Description | The system should detect duplicate complaints by comparing location, complaint type, description, and images against existing nearby complaints, linking or merging duplicates with the main complaint instead of creating independent cases. |

| Field / Information | Purpose |
| --- | --- |
| Complaint ID | New complaint being checked |
| Matched Complaint ID | Existing complaint identified as a possible duplicate |
| Match Criteria | Location proximity, type match, description similarity, image similarity |
| Reporter Count | Number of citizens who reported the same issue |
| Merge Status | Linked, merged, or independent |

| Rule | Description |
| --- | --- |
| BR-001 | Duplicate detection should compare location, type, description, and images. |
| BR-002 | Merged complaints must retain a reference to the main complaint. |
| BR-003 | The number of citizens reporting the same issue must be tracked even after merging. |
| BR-004 | Only the main complaint should be routed to the department for action. |
| BR-005 | Duplicate detection results should be reviewable by ground-level employees. |

| Item | Details |
| --- | --- |
| Feature | Priority Assessment & Assignment |
| Primary Actor | System / Supervisor |
| Description | The system should identify the geographical location of a complaint, determine the responsible municipality/department, and assign the complaint to the appropriate employee so complaints reach the correct authority without manual routing. |

| Field / Information | Purpose |
| --- | --- |
| Complaint Location | Pinned location of the issue |
| Responsible Municipality/Office | Determined jurisdiction |
| Assigned Department | Department responsible for the complaint type |
| Assigned Employee | Ground-level employee handling the complaint |
| Assignment Date | Date the complaint was routed |

| Rule | Description |
| --- | --- |
| BR-001 | Department assignment must be based on both location and complaint type. |
| BR-002 | The responsible department must be notified immediately upon assignment. |
| BR-003 | A supervisor can reassign a complaint to a different employee within the department. |
| BR-004 | Department A must not be able to view or act on Department B's complaints. |
| BR-005 | Assignment history must be preserved in the complaint record. |

| Item | Details |
| --- | --- |
| Feature | Verification & Resolution |
| Primary Actor | Ground-Level Employee |
| Description | A ground-level employee should be able to view, inspect, and verify whether a reported complaint is valid, marking it Verified or Invalid with supporting remarks. |

| Field / Information | Purpose |
| --- | --- |
| Complaint Details | Type, description, photos, location |
| Site Inspection Notes | Employee's on-site observations |
| Verification Result | Verified or Invalid |
| Verification Remarks | Explanation supporting the decision |
| Verified By / On | Audit information |

| Rule | Description |
| --- | --- |
| BR-001 | Only employees within the assigned department can verify a complaint. |
| BR-002 | Verification remarks are mandatory for both Verified and Invalid outcomes. |
| BR-003 | Complaint status must follow the flow: Submitted → Under Verification → Verified. |
| BR-004 | Verification actions must be captured in the audit log. |
| BR-005 | Invalid complaints should be closed and communicated to the citizen with a reason. |

| Item | Details |
| --- | --- |
| Feature | Verification & Resolution |
| Primary Actor | Ground-Level Employee |
| Description | The assigned employee should be able to update progress, add remarks, set an expected completion date, and mark a verified complaint as resolved with uploaded proof. |

| Field / Information | Purpose |
| --- | --- |
| Progress Update | Current status of the resolution work |
| Remarks | Notes on work performed |
| Expected Completion Date | Estimated date of resolution |
| Resolution Details | Description of the fix carried out |
| Resolution Proof | Photo/document evidence of completion |

| Rule | Description |
| --- | --- |
| BR-001 | Resolution proof is mandatory before a complaint can be marked Resolved. |
| BR-002 | Only the assigned employee (or supervisor) can update a complaint's resolution status. |
| BR-003 | Expected completion date changes must be logged and trigger a notification. |
| BR-004 | Supervisors must be able to monitor whether complaints are resolved within deadline. |
| BR-005 | Resolved complaints move to Closed only after citizen confirmation or a defined closure window. |

| Item | Details |
| --- | --- |
| Feature | Verification & Resolution |
| Primary Actor | Citizen / User |
| Description | Citizens should be able to track their complaints using the Complaint ID to see current status, assigned department, progress updates, and resolution details. |

| Field / Information | Purpose |
| --- | --- |
| Complaint ID | Unique identifier used for tracking |
| Current Status | Submitted, Under Verification, Verified, Assigned, In Progress, Resolved, Closed |
| Assigned Department / Officer | Entity handling the complaint |
| Progress Updates | History of status changes and remarks |
| Expected Completion Date | Estimated resolution date |
| Resolution Details & Proof | Evidence of completion |

| Rule | Description |
| --- | --- |
| BR-001 | Citizens can track only complaints linked to their account or a valid Complaint ID. |
| BR-002 | Tracking should reflect the latest status in real time. |
| BR-003 | Merged complaints should display the main complaint's progress. |
| BR-004 | Resolution proof should be visible once the complaint is resolved. |
| BR-005 | Closed complaints should remain viewable in the citizen's complaint history. |

| Item | Details |
| --- | --- |
| Feature | Notifications & Dashboards |
| Primary Actor | System |
| Description | The system should automatically notify citizens and departments when a complaint is submitted, verified, assigned, changes status, has a deadline change, is resolved, or is closed. |

| Field / Information | Purpose |
| --- | --- |
| Recipient | Citizen or department to be notified |
| Trigger Event | Submission, verification, assignment, status change, deadline change, resolution, closure |
| Notification Channel | Email, SMS, in-app |
| Message Content | Notification text |
| Sent Date / Time | Timestamp of the notification |

| Rule | Description |
| --- | --- |
| BR-001 | Notifications must be triggered automatically by defined status-change events. |
| BR-002 | Notification delivery failures should be logged for retry. |
| BR-003 | Citizens should be able to view all notifications within their dashboard. |
| BR-004 | Departments must be notified immediately upon complaint assignment. |
| BR-005 | Notification channel preferences should be configurable where supported. |

| Item | Details |
| --- | --- |
| Feature | Notifications & Dashboards |
| Primary Actor | Citizen / User |
| Description | Citizens should have a personal dashboard showing their complaints, pending/completed status, complaints near their location, and notifications. |

| Field / Information | Purpose |
| --- | --- |
| My Complaints | List of complaints submitted by the citizen |
| Pending / Completed Complaints | Status-based groupings |
| Complaint Status | Current stage of each complaint |
| Complaints Near My Location | Nearby reported issues |
| Notifications | Recent alerts and updates |

| Rule | Description |
| --- | --- |
| BR-001 | Citizens can only view their own complaints and public nearby complaints. |
| BR-002 | Dashboard data must reflect the latest complaint status. |
| BR-003 | Nearby complaints should exclude sensitive personal details of other citizens. |
| BR-004 | Notifications on the dashboard should be marked read/unread. |

| Item | Details |
| --- | --- |
| Feature | Notifications & Dashboards |
| Primary Actor | Supervisor / Department Admin |
| Description | Department staff should have a dashboard showing total, pending, completed, high-priority, and overdue complaints along with employee performance, so department operations can be monitored effectively. |

| Field / Information | Purpose |
| --- | --- |
| Total / Pending / Completed Complaints | Status-based counts |
| High-Priority Complaints | Complaints flagged High Priority |
| Complaints by Category / Location | Breakdown views |
| Assigned / Overdue Complaints | Workload and deadline tracking |
| Employee Performance | Progress by ground-level employee |

| Rule | Description |
| --- | --- |
| BR-001 | A department can view only complaints assigned to it. |
| BR-002 | Overdue complaints must be identifiable based on expected completion date. |
| BR-003 | Dashboard figures must be based on the latest complaint status. |
| BR-004 | Department Admins can view all employees within their department; Supervisors view their assigned team. |
| BR-005 | Dashboard data should support export for offline review. |

| Item | Details |
| --- | --- |
| Feature | Notifications & Dashboards |
| Primary Actor | System Admin |
| Description | The System Admin should be able to manage users, departments, roles, and permissions, and monitor system-wide statistics from a central admin dashboard. |

| Field / Information | Purpose |
| --- | --- |
| User Management | Create, update, deactivate user accounts |
| Department Management | Create/manage departments |
| Role & Permission Assignment | Manage access levels |
| Employee Management | Manage ground-level staff records |
| System-Wide Statistics | Complaint volumes and performance across departments |

| Rule | Description |
| --- | --- |
| BR-001 | Only the System Admin can manage system-wide roles, permissions, and departments. |
| BR-002 | All administrative actions must be captured in the audit log. |
| BR-003 | Department creation/edits should not disrupt existing complaint assignments. |
| BR-004 | System-wide statistics must be based on the latest data across all departments. |

| Item | Details |
| --- | --- |
| Feature | Reports & Statistics |
| Primary Actor | Department Admin / System Admin |
| Description | The system should generate reports on complaint volumes, categories, locations, departments, priorities, and average resolution times, so administrators and leadership can evaluate performance. |

| Field / Information | Purpose |
| --- | --- |
| Complaint Counts | Total, pending, completed, rejected/invalid |
| Category / Location / Department Breakdown | Distribution views |
| High-Priority Complaints | Count of high-impact complaints |
| Average Resolution Time | Performance metric |
| Employee / Department Performance | Comparative performance data |

| Rule | Description |
| --- | --- |
| BR-001 | Reports should reflect the latest complaint and resolution data. |
| BR-002 | Department Admins can view reports only for their own department; System Admin can view all departments. |
| BR-003 | Average resolution time should be calculated from verification to closure. |
| BR-004 | Report exports must follow the requesting user's access permissions. |
| BR-005 | Rejected/invalid complaints should be reported separately from resolved complaints. |

| Feature | Role | User Story / Capability | Priority |
| --- | --- | --- | --- |
| User Management | Citizen / User | Register and log in | P1 |
| User Management | System Admin | Manage roles and permissions | P1 |
| Complaint Registration & Classification | Citizen / User | Submit complaint | P1 |
| Complaint Registration & Classification | System | AI-based complaint classification | P1 |
| Priority Assessment & Assignment | System | AI-based priority assessment | P1 |
| Priority Assessment & Assignment | System | Duplicate complaint detection | P2 |
| Priority Assessment & Assignment | System / Supervisor | Location-based department assignment | P1 |
| Complaint Verification & Resolution | Ground-Level Employee | Verify complaint | P1 |
| Complaint Verification & Resolution | Ground-Level Employee | Resolve complaint | P1 |
| Complaint Verification & Resolution | Citizen / User | Track complaint | P1 |
| Notifications & Dashboards | System | Send notifications | P1 |
| Notifications & Dashboards | Citizen / User | View citizen dashboard | P1 |
| Notifications & Dashboards | Supervisor / Dept Admin | View department dashboard | P1 |
| Notifications & Dashboards | System Admin | View admin dashboard | P2 |
| Reports & Statistics | Dept Admin / System Admin | Generate reports & statistics | P2 |
