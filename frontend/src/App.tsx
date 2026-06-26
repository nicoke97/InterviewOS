import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { LevelRoadmap } from './pages/LevelRoadmap';
import { KumonSession } from './pages/Kumon';
import { Checkpoint } from './pages/Checkpoint';
import { Exam } from './pages/Exam';
import { Settings } from './pages/Settings';
import { OrientadorPage } from './pages/Orientador';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/orientador" element={<OrientadorPage />} />
          <Route path="/settings" element={<Settings />} />

          <Route path="/kumon" element={<Navigate to="/a/roadmap" replace />} />
          <Route path="/:level" element={<RoadmapRedirect />} />
          <Route path="/:level/roadmap" element={<LevelRoadmap />} />
          <Route path="/orientador/:planId/:index" element={<KumonSession />} />
          <Route path="/:level/kumon" element={<KumonSession />} />
          <Route path="/:level/checkpoint/:block" element={<Checkpoint />} />
          <Route path="/:level/exam" element={<Exam />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

import { useParams } from 'react-router-dom';

function RoadmapRedirect() {
  const { level } = useParams();
  return <Navigate to={`/${level || 'a'}/roadmap`} replace />;
}

export default App;
