self.addEventListener('activate', ev => {
    ev.waitUntil(clients.claim())
})

self.addEventListener('push', event => {
    const data = event.data.json()

    self.registration.showNotification(data.title, data)
})
