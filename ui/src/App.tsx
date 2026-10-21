import { HashRouter, Routes, Route } from 'react-router-dom'
import TempleList from './pages/TempleList'
import TempleDetail from './pages/TempleDetail'
import EditPage from './pages/EditPage'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<TempleList />} />
        <Route path="/temples/:id" element={<TempleDetail />} />
        <Route path="/edit" element={<EditPage />} />
      </Routes>
    </HashRouter>
  )
}
