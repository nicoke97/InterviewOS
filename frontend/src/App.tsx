import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Kumon } from './pages/Kumon';
import { LeetCode } from './pages/LeetCode';
import { Interview } from './pages/Interview';
import { Settings } from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/kumon" element={<Kumon />} />
          <Route path="/leetcode" element={<LeetCode />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/odoo" element={<Interview category="odoo" />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
