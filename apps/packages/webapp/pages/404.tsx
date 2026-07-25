import type { ReactElement } from 'react';
import React, { useEffect, useRef } from 'react';
import Custom404 from '@shikkhahub/shared/src/components/Custom404';
import { ErrorBoundary } from '@shikkhahub/shared/src/components/ErrorBoundary';
import { NextSeo } from 'next-seo';
import { LogEvent } from '@shikkhahub/shared/src/lib/log';
import { useLogContext } from '@shikkhahub/shared/src/contexts/LogContext';

export default function Custom404Seo(): ReactElement {
  const { logEvent } = useLogContext();
  const logImpression = useRef(false);

  useEffect(() => {
    if (logImpression.current) {
      return;
    }

    logEvent({
      event_name: LogEvent.View404Page,
    });
    logImpression.current = true;
  }, [logEvent, logImpression]);

  return (
    <ErrorBoundary feature="404-page">
      <Custom404>
        <NextSeo title="Page not found" nofollow noindex />
      </Custom404>
    </ErrorBoundary>
  );
}
