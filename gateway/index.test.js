const test = require('node:test');
const assert = require('node:assert');

// Extract the function logic without needing to run the full server.
// Since this is in the same directory, we'll define the test helpers inline.

const CANONICAL_HOST = 'armarequipos.com';
const REDIRECT_HOSTS = new Set([
  'armarequipos.up.railway.app',
  'www.armarequipos.com'
]);

/**
 * Determines if a redirect to the canonical host is needed.
 * This is a copy of the function from index.js for testing purposes.
 * @param {object} req - Express request object
 * @returns {string|null} - Redirect URL if redirect is needed, null otherwise
 */
function getCanonicalRedirectTarget(req) {
  const host = req.headers.host;

  if (!host) {
    return null;
  }

  // Strip port suffix from host header (e.g., "example.com:3000" -> "example.com")
  const normalizedHost = host.split(':')[0];

  if (REDIRECT_HOSTS.has(normalizedHost)) {
    // Preserve the original path and query string in the redirect target
    const path = req.originalUrl || req.url || '/';
    return `https://${CANONICAL_HOST}${path}`;
  }

  return null;
}

test('getCanonicalRedirectTarget', async (t) => {
  await t.test('should redirect armarequipos.up.railway.app with query string', () => {
    const req = {
      headers: { host: 'armarequipos.up.railway.app' },
      originalUrl: '/jugadores?club=5'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, 'https://armarequipos.com/jugadores?club=5');
  });

  await t.test('should redirect www.armarequipos.com to canonical', () => {
    const req = {
      headers: { host: 'www.armarequipos.com' },
      originalUrl: '/'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, 'https://armarequipos.com/');
  });

  await t.test('should not redirect canonical host', () => {
    const req = {
      headers: { host: 'armarequipos.com' },
      originalUrl: '/jugadores'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, null);
  });

  await t.test('should not crash when host is undefined', () => {
    const req = {
      headers: {},
      originalUrl: '/jugadores'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, null);
  });

  await t.test('should strip port suffix from host header', () => {
    const req = {
      headers: { host: 'armarequipos.up.railway.app:3000' },
      originalUrl: '/jugadores'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, 'https://armarequipos.com/jugadores');
  });

  await t.test('should preserve complex query strings', () => {
    const req = {
      headers: { host: 'www.armarequipos.com' },
      originalUrl: '/jugadores?club=5&name=test&active=true'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(
      result,
      'https://armarequipos.com/jugadores?club=5&name=test&active=true'
    );
  });

  await t.test('should fall back to req.url if originalUrl is missing', () => {
    const req = {
      headers: { host: 'armarequipos.up.railway.app' },
      url: '/matches'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, 'https://armarequipos.com/matches');
  });

  await t.test('should return / as default path', () => {
    const req = {
      headers: { host: 'www.armarequipos.com' }
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, 'https://armarequipos.com/');
  });

  await t.test('should not redirect non-listed hosts', () => {
    const req = {
      headers: { host: 'example.com' },
      originalUrl: '/test'
    };
    const result = getCanonicalRedirectTarget(req);
    assert.strictEqual(result, null);
  });
});
