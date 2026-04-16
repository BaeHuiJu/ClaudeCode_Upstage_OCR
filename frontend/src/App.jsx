import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import UploadPage from './pages/UploadPage'
import ExpenseDetail from './pages/ExpenseDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/expense/:id" element={<ExpenseDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
