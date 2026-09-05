import { Routes, Route } from "react-router";
import DashboardPage from "./pages/DashboardPage";
import ReviewPage from "./pages/ReviewPage";
import AuthPage from "./pages/AuthPage";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AuthPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/review" element={<ReviewPage />} />
      </Route>
    </Routes>
  );
}