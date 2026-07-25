import type { ReactElement, ReactNode } from 'react';
import React, { useContext, useEffect } from 'react';
import { useRouter } from 'next/router';
import AuthContext from '@shikkhahub/shared/src/contexts/AuthContext';
import { AFTER_AUTH_PARAM } from '@shikkhahub/shared/src/components/auth/common';
import { onboardingUrl } from '@shikkhahub/shared/src/lib/constants';

export interface ProtectedPageProps {
  children: ReactNode;
  fallback?: ReactNode;
  shouldFallback?: boolean;
}

const getOnboardingRedirect = (path: string): string =>
  `${onboardingUrl}?${new URLSearchParams({
    [AFTER_AUTH_PARAM]: path,
  }).toString()}`;

function ProtectedPage({
  children,
  fallback,
  shouldFallback,
}: ProtectedPageProps): ReactElement {
  const router = useRouter();
  const { tokenRefreshed, user } = useContext(AuthContext);

  useEffect(() => {
    if (tokenRefreshed && !user) {
      router.replace(getOnboardingRedirect(router.asPath || '/'));
    }
    // @NOTE see https://shikkhahub.atlassian.net/l/cp/dK9h1zoM
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, tokenRefreshed, user]);

  return <>{shouldFallback ? fallback : children}</>;
}

export default ProtectedPage;
