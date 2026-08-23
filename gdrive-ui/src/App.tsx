import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { AppShell } from "./components/AppShell"
import { LandingPage } from "./pages/LandingPage"
import { DrivesPage } from "./pages/DrivesPage"
import { BrowsePage } from "./pages/BrowsePage"
import { GeneratePage } from "./pages/GeneratePage"
import { TrashPage } from "./pages/TrashPage"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/drives"
          element={
            <AppShell>
              <DrivesPage />
            </AppShell>
          }
        />
        <Route path="/drives/:driveId" element={<Navigate to="browse" replace />} />
        <Route
          path="/drives/:driveId/browse/*"
          element={
            <AppShell>
              <BrowsePage />
            </AppShell>
          }
        />
        <Route
          path="/drives/:driveId/generate"
          element={
            <AppShell>
              <GeneratePage />
            </AppShell>
          }
        />
        <Route
          path="/drives/:driveId/trash"
          element={
            <AppShell>
              <TrashPage />
            </AppShell>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
