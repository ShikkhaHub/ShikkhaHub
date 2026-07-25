import type { ReactElement, ReactNode } from 'react';
import React, { useEffect } from 'react';
import { cloudinaryPlusBackground } from '@shikkhahub/shared/src/lib/image';
import { PaymentContextProvider } from '@shikkhahub/shared/src/contexts/payment';
import { useAuthContext } from '@shikkhahub/shared/src/contexts/AuthContext';
import { onboardingUrl } from '@shikkhahub/shared/src/lib/constants';
import { useRouter } from 'next/router';
import { useGrowthBookContext } from '@shikkhahub/shared/src/components/GrowthBookProvider';
import {
  ThemeMode,
  useSettingsContext,
} from '@shikkhahub/shared/src/contexts/SettingsContext';
import type { MainFeedPageProps } from '../MainFeedPage';
import { PlusHeader } from './PlusHeader';

export default function PlusLayout({
  children,
}: MainFeedPageProps): ReactElement | null {
  const { user, isAuthReady } = useAuthContext();
  const { growthbook } = useGrowthBookContext();
  const router = useRouter();
  const { applyThemeMode } = useSettingsContext();

  const isPageReady = growthbook?.ready && router?.isReady && isAuthReady;

  const shouldRedirectOnboarding = !user && isPageReady;

  useEffect(() => {
    if (!shouldRedirectOnboarding) {
      return;
    }

    router.push(`${onboardingUrl}`);
  }, [router, shouldRedirectOnboarding]);

  useEffect(() => {
    applyThemeMode(ThemeMode.Dark);
    return () => {
      applyThemeMode();
    };
  }, [applyThemeMode]);

  if (!isPageReady || shouldRedirectOnboarding) {
    return null;
  }

  return (
    <main className="relative flex min-h-dvh flex-col">
      <img
        src={cloudinaryPlusBackground}
        alt="Plus background"
        className="absolute inset-0 -z-1 h-full w-full object-cover"
        aria-hidden
      />
      <PlusHeader />
      {children}
    </main>
  );
}

export function getPlusLayout(page: ReactNode): ReactNode {
  return (
    <PaymentContextProvider>
      <PlusLayout>{page}</PlusLayout>
    </PaymentContextProvider>
  );
}
