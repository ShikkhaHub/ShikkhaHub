import { postWindowMessage, isPWA } from '@shikkhahub/shared/src/lib/func';
import { AuthEvent } from '@shikkhahub/shared/src/lib/auth';
import type { ReactElement } from 'react';
import { useEffect } from 'react';

function ErrorPage(): ReactElement | null {
  useEffect(() => {
    const urlSearchParams = new URLSearchParams(window.location.search);
    const params = Object.fromEntries(urlSearchParams.entries());
    postWindowMessage(AuthEvent.Error, params);
    if (!isPWA()) {
      window.close();
    }
  }, []);

  return null;
}

export default ErrorPage;
