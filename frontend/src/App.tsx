import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { NetworkTypesPage } from './pages/NetworkTypesPage'
import { NetworksPage } from './pages/NetworksPage'
import { NetworkDetailPage } from './pages/NetworkDetailPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter basename="/">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/network-types"
            element={
              <ProtectedRoute>
                <NetworkTypesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/networks"
            element={
              <ProtectedRoute>
                <NetworksPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/networks/:id"
            element={
              <ProtectedRoute>
                <NetworkDetailPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}


export default App
