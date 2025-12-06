export function notify(title, body) {
  try {
    if (window?.Notification) {
      if (Notification.permission === 'granted') {
        new Notification(title, { body })
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then((perm) => {
          if (perm === 'granted') new Notification(title, { body })
        })
      }
    } else {
      console.log(`[Notify] ${title}: ${body}`)
    }
  } catch (e) {
    console.log(`[Notify error] ${e}`)
  }
}

export function notifyHighCpu(cpuPercent) {
  notify('High CPU Usage', `CPU at ${Number(cpuPercent).toFixed(1)}%`)
}

export function notifyHighRam(memPercent) {
  notify('High Memory Usage', `RAM at ${Number(memPercent).toFixed(1)}%`)
}

export function notifyError(message) {
  notify('Backend Error', String(message || 'An error occurred'))
}

export function notifyConfigSaved() {
  notify('Settings Saved', 'Configuration has been updated successfully')
}