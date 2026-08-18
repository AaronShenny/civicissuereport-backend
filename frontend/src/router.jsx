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
import AdminOverview from './pages/AdminOverview';

// Legacy AssetFlow Pages
import Assets from './pages/Assets';
import AssetDetail from './pages/AssetDetail';
import AssetForm from './pages/AssetForm';
import Categories from './pages/Categories';
import Assignments from './pages/Assignments';
import Maintenance from './pages/Maintenance';
import Reports from './pages/Reports';
import Users from './pages/Users';
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
      { path: 'admin/overview', element: <AdminOverview /> },

      // Legacy AssetFlow Routes
      { path: 'assets', element: <Assets /> },
      { path: 'assets/new', element: <AssetForm /> },
      { path: 'assets/:id', element: <AssetDetail /> },
      { path: 'assets/:id/edit', element: <AssetForm /> },
      { path: 'categories', element: <Categories /> },
      { path: 'assignments', element: <Assignments /> },
      { path: 'maintenance', element: <Maintenance /> },
      { path: 'reports', element: <Reports /> },
      { path: 'users', element: <Users /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
