import { Routes, Route } from "react-router";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";
import ReviewPage from "./pages/ReviewPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/review" element={<ReviewPage />} />
    </Routes>
  );
}