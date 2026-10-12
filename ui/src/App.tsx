import { HashRouter, Routes, Route } from 'react-router-dom'
import TempleList from './pages/TempleList'
import TempleDetail from './pages/TempleDetail'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<TempleList />} />
        <Route path="/temples/:id" element={<TempleDetail />} />
      </Routes>
    </HashRouter>
  )
}
