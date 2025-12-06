import { useEffect, useState } from "react"

export default function SettingsPanel({ baseUrl = "http://127.0.0.1:6060" }) {
  const [autoUpdate, setAutoUpdate] = useState(false)
  const [status, setStatus] = useState("")

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(baseUrl + "/config")
        const data = await res.json()
        setAutoUpdate(Boolean(data.auto_update))
      } catch {
        console.warn("Failed to fetch config")
      }
    })()
  }, [baseUrl])

  async function toggleUpdate() {
    try {
      const res = await fetch(baseUrl + "/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_update: !autoUpdate })
      })
      const data = await res.json()
      setAutoUpdate(Boolean(data.auto_update))
      setStatus("Saved")
      setTimeout(() => setStatus(""), 1500)
    } catch (e) {
      setStatus("Failed to save")
      console.error(e)
    }
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">Jessica Settings</h2>
      <label>
        <input type="checkbox" checked={autoUpdate} onChange={toggleUpdate} /> Enable Auto Update
      </label>
      {status && <p className="status">{status}</p>}
    </div>
  )
}