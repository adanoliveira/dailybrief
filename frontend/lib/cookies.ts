/**
 * Set a cookie with the given name, value, and days to expiration
 */
export function setCookie(name: string, value: string, days: number): void {
  const expirationDate = new Date();
  expirationDate.setDate(expirationDate.getDate() + days);
  
  const cookieValue = encodeURIComponent(value) + 
    ((days) ? `; expires=${expirationDate.toUTCString()}` : '') + 
    '; path=/; SameSite=Lax';
  
  document.cookie = `${name}=${cookieValue}`;
}

/**
 * Get a cookie by name
 */
export function getCookie(name: string): string | null {
  const nameEQ = `${name}=`;
  const cookies = document.cookie.split(';');
  
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i].trim();
    if (cookie.indexOf(nameEQ) === 0) {
      return decodeURIComponent(cookie.substring(nameEQ.length, cookie.length));
    }
  }
  
  return null;
}

/**
 * Delete a cookie by setting its expiration in the past
 */
export function deleteCookie(name: string): void {
  document.cookie = `${name}=; Max-Age=-99999999; path=/`;
} 