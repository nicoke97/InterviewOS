import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { LevelRoadmap } from './pages/LevelRoadmap';
import { KumonSession } from './pages/Kumon';
import { Checkpoint } from './pages/Checkpoint';
import { Exam } from './pages/Exam';
import { Settings } from './pages/Settings';
import { OrientadorPage } from './pages/Orientador';
import { LeetcodeRoadmap } from './pages/LeetcodeRoadmap';
import { LeetcodePractice } from './pages/LeetcodePractice';
import { LeetcodeSession } from './pages/LeetcodeSession';
import { StoriesPage } from './pages/Stories';
import { ReturnExamPage } from './pages/ReturnExam';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/return-exam" element={<ReturnExamPage />} />
          <Route path="/orientador" element={<OrientadorPage />} />
          <Route path="/settings" element={<Settings />} />

          <Route path="/stories" element={<StoriesPage />} />
          <Route path="/projects" element={<Navigate to="/stories" replace />} />

          <Route path="/leetcodes" element={<LeetcodeRoadmap />} />
          <Route path="/leetcodes/orientador/:planId/:index" element={<LeetcodeSession />} />
          <Route path="/leetcodes/:problemId" element={<LeetcodePractice />} />

          <Route path="/kumon" element={<Navigate to="/a/roadmap" replace />} />
          <Route path="/orientador/:planId/:index" element={<KumonSession />} />
          <Route path="/:level/roadmap" element={<LevelRoadmap />} />
          <Route path="/:level/kumon" element={<KumonSession />} />
          <Route path="/:level/checkpoint/:block" element={<Checkpoint />} />
          <Route path="/:level/exam" element={<Exam />} />
          <Route path="/:level" element={<RoadmapRedirect />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

function RoadmapRedirect() {
  const { level } = useParams();
  return <Navigate to={`/${level || 'a'}/roadmap`} replace />;
}

export default App;
