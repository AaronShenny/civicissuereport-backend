import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from './auth/ProtectedRoute';

// Layout
import AppLayout from './layouts/AppLayout';

// Pages
import Landing from './pages/Landing';
import TrackComplaint from './pages/TrackComplaint';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

// Civic Pages
import SubmitComplaint from './pages/SubmitComplaint';
import MyComplaints from './pages/MyComplaints';
import ComplaintDetail from './pages/ComplaintDetail';
import EmployeeComplaints from './pages/EmployeeComplaints';
import SupervisorUnassigned from './pages/SupervisorUnassigned';
import SupervisorComplaints from './pages/SupervisorComplaints';
import DepartmentComplaints from './pages/DepartmentComplaints';
import DepartmentEmployees from './pages/DepartmentEmployees';
import DepartmentPerformance from './pages/DepartmentPerformance';
import AdminOverview from './pages/AdminOverview';
import AdminUsers from './pages/admin/AdminUsers';
import AdminDepartments from './pages/admin/AdminDepartments';
import AdminCategories from './pages/admin/AdminCategories';
import AdminCategoryRouting from './pages/admin/AdminCategoryRouting';
import AdminRoles from './pages/admin/AdminRoles';
import AdminPriorityRules from './pages/admin/AdminPriorityRules';
import AdminAssignmentRules from './pages/admin/AdminAssignmentRules';
import AdminAuditLogs from './pages/admin/AdminAuditLogs';
import AdminReports from './pages/admin/AdminReports';
import AdminSettings from './pages/admin/AdminSettings';
import Settings from './pages/Settings';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/track',
    element: <TrackComplaint />,
  },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: 'dashboard', element: <Dashboard /> },
      
      // Civic Routes
      { path: 'complaints/new', element: <SubmitComplaint /> },
      { path: 'complaints', element: <MyComplaints /> },
      { path: 'complaints/:id', element: <ComplaintDetail /> },
      { path: 'employee/complaints', element: <EmployeeComplaints /> },
      { path: 'supervisor/unassigned', element: <SupervisorUnassigned /> },
      { path: 'supervisor/complaints', element: <SupervisorComplaints /> },
      { path: 'department/complaints', element: <DepartmentComplaints /> },
      { path: 'department/employees', element: <DepartmentEmployees /> },
      { path: 'department/performance', element: <DepartmentPerformance /> },
      { path: 'admin/overview', element: <AdminOverview /> },
      { path: 'admin/users', element: <AdminUsers /> },
      { path: 'admin/departments', element: <AdminDepartments /> },
      { path: 'admin/categories', element: <AdminCategories /> },
      { path: 'admin/category-routing', element: <AdminCategoryRouting /> },
      { path: 'admin/roles', element: <AdminRoles /> },
      { path: 'admin/priority-rules', element: <AdminPriorityRules /> },
      { path: 'admin/assignment-rules', element: <AdminAssignmentRules /> },
      { path: 'admin/audit-logs', element: <AdminAuditLogs /> },
      { path: 'admin/reports', element: <AdminReports /> },
      { path: 'admin/settings', element: <AdminSettings /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
