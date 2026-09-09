import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { Layout } from './components/Layout';
import { useI18n } from './i18n/context';

const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })));
const LevelRoadmap = lazy(() => import('./pages/LevelRoadmap').then((m) => ({ default: m.LevelRoadmap })));
const KumonSession = lazy(() => import('./pages/Kumon').then((m) => ({ default: m.KumonSession })));
const Checkpoint = lazy(() => import('./pages/Checkpoint').then((m) => ({ default: m.Checkpoint })));
const Exam = lazy(() => import('./pages/Exam').then((m) => ({ default: m.Exam })));
const Settings = lazy(() => import('./pages/Settings').then((m) => ({ default: m.Settings })));
const OrientadorPage = lazy(() => import('./pages/Orientador').then((m) => ({ default: m.OrientadorPage })));
const LeetcodeRoadmap = lazy(() => import('./pages/LeetcodeRoadmap').then((m) => ({ default: m.LeetcodeRoadmap })));
const LeetcodePractice = lazy(() => import('./pages/LeetcodePractice').then((m) => ({ default: m.LeetcodePractice })));
const LeetcodeSession = lazy(() => import('./pages/LeetcodeSession').then((m) => ({ default: m.LeetcodeSession })));
const StoriesPage = lazy(() => import('./pages/Stories').then((m) => ({ default: m.StoriesPage })));
const ReturnExamPage = lazy(() => import('./pages/ReturnExam').then((m) => ({ default: m.ReturnExamPage })));
const SdeCardsPage = lazy(() => import('./pages/SdeCards').then((m) => ({ default: m.SdeCardsPage })));
const SdeSectionPage = lazy(() => import('./pages/SdeSection').then((m) => ({ default: m.SdeSectionPage })));
const SdeAlgoPage = lazy(() => import('./pages/SdeAlgo').then((m) => ({ default: m.SdeAlgoPage })));
const SdeVoicePage = lazy(() => import('./pages/SdeVoice').then((m) => ({ default: m.SdeVoicePage })));
const SdeSqlPage = lazy(() => import('./pages/SdeSql').then((m) => ({ default: m.SdeSqlPage })));
const SdePackPage = lazy(() => import('./pages/SdeSql').then((m) => ({ default: m.SdePackPage })));
const SdeDebugPage = lazy(() => import('./pages/SdeDebug').then((m) => ({ default: m.SdeDebugPage })));
const SdeReadingPage = lazy(() => import('./pages/SdeReading').then((m) => ({ default: m.SdeReadingPage })));

function PageFallback() {
  const { t } = useI18n();
  return <p className="text-text-muted">{t('common.loading')}</p>;
}

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sde/cards" element={<SdeCardsPage />} />
            <Route path="/sde/reading/:weekId" element={<SdeReadingPage />} />
            <Route path="/sde/section/:id" element={<SdeSectionPage />} />
            <Route path="/sde/algo/:algoId/:lang/:sheetId" element={<SdeAlgoPage />} />
            <Route path="/sde/voice" element={<SdeVoicePage />} />
            <Route path="/sde/sql/:id" element={<SdeSqlPage />} />
            <Route path="/sde/pack" element={<SdePackPage />} />
            <Route path="/sde/debug/:bugId" element={<SdeDebugPage />} />
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
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}

function RoadmapRedirect() {
  const { level } = useParams();
  return <Navigate to={`/${level || 'a'}/roadmap`} replace />;
}

export default App;
