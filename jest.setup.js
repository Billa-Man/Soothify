import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      pathname: '/',
      query: {},
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock environment variables for tests
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:3000'
process.env.OPENAI_API_KEY = 'test-key'
process.env.MONGODB_URI = 'mongodb://localhost:27017/test'
process.env.DB_NAME = 'test'

// Mock Web APIs that might not be available in test environment
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {
    return null
  }
  disconnect() {
    return null
  }
  unobserve() {
    return null
  }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {
    return null
  }
  disconnect() {
    return null
  }
  unobserve() {
    return null
  }
}

// Mock MediaRecorder for audio tests
global.MediaRecorder = class MediaRecorder {
  constructor() {
    this.state = 'inactive'
    this.mimeType = 'audio/webm'
  }
  start() {
    this.state = 'recording'
  }
  stop() {
    this.state = 'inactive'
  }
  addEventListener() {}
  removeEventListener() {}
}

// Mock getUserMedia for audio recording tests
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: jest.fn(() =>
      Promise.resolve({
        getTracks: () => [{ stop: jest.fn() }],
      })
    ),
  },
})

// Mock Web APIs for Node.js environment
global.Response = class Response {
  constructor(body, options = {}) {
    this.body = body
    this.status = options.status || 200
    this.headers = new Map(Object.entries(options.headers || {}))
    this.ok = this.status >= 200 && this.status < 300
  }

  json() {
    return Promise.resolve(JSON.parse(this.body))
  }

  text() {
    return Promise.resolve(this.body)
  }

  arrayBuffer() {
    return Promise.resolve(new ArrayBuffer(8))
  }
}

global.Request = class Request {
  constructor(url, options = {}) {
    this.url = url
    this.method = options.method || 'GET'
    this.headers = new Map(Object.entries(options.headers || {}))
  }
}

global.URL = class URL {
  constructor(url) {
    this.href = url
    this.pathname = new URL(url).pathname
    this.searchParams = new URLSearchParams(new URL(url).search)
  }
}

global.URLSearchParams = class URLSearchParams {
  constructor(params) {
    this.params = new Map()
    if (typeof params === 'string') {
      params.split('&').forEach(pair => {
        const [key, value] = pair.split('=')
        this.params.set(decodeURIComponent(key), decodeURIComponent(value || ''))
      })
    }
  }

  get(key) {
    return this.params.get(key) || null
  }

  toString() {
    return Array.from(this.params.entries())
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&')
  }
}

global.FormData = class FormData {
  constructor() {
    this.data = new Map()
  }

  append(key, value) {
    this.data.set(key, value)
  }

  get(key) {
    return this.data.get(key) || null
  }
}

global.File = class File {
  constructor(chunks, filename, options = {}) {
    this.name = filename
    this.type = options.type || ''
    this.size = chunks.reduce((size, chunk) => size + chunk.length, 0)
  }
}
