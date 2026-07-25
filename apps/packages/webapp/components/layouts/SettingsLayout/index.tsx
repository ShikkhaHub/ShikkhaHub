import type { PropsWithChildren, ReactElement, ReactNode } from 'react';
import React, { useContext, useEffect } from 'react';
import AuthContext from '@shikkhahub/shared/src/contexts/AuthContext';
import {
  generateQueryKey,
  RequestKey,
} from '@shikkhahub/shared/src/lib/query';
import { useViewSize, ViewSize } from '@shikkhahub/shared/src/hooks';
import { useQueryState } from '@shikkhahub/shared/src/hooks/utils/useQueryState';
import { useRouter } from 'next/router';
import { AuthTriggers } from '@shikkhahub/shared/src/lib/auth';
import AuthOptions from '@shikkhahub/shared/src/components/auth/AuthOptions';
import useAuthForms from '@shikkhahub/shared/src/hooks/useAuthForms';
import dynamic from 'next/dynamic';
import {
  Typography,
  TypographyColor,
  TypographyTag,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';
import {
  Button,
  ButtonSize,
  ButtonVariant,
} from '@shikkhahub/shared/src/components/buttons/Button';
import { ArrowIcon } from '@shikkhahub/shared/src/components/icons';
import Link from '@shikkhahub/shared/src/components/utilities/Link';
import { webappUrl } from '@shikkhahub/shared/src/lib/constants';
import { BuyCreditsButton } from '@shikkhahub/shared/src/components/credit/BuyCreditsButton';
import { useCanPurchaseCores } from '@shikkhahub/shared/src/hooks/useCoresFeature';
import { getPathnameWithQuery } from '@shikkhahub/shared/src/lib';
import { Origin } from '@shikkhahub/shared/src/lib/log';
import { getLayout as getFooterNavBarLayout } from '../FooterNavBarLayout';
import { getLayout as getMainLayout } from '../MainLayout';

const ProfileSettingsMenuMobile = dynamic(
  () =>
    import(
      /* webpackChunkName: "profileSettingsMenuMobile" */ '@shikkhahub/shared/src/components/profile/ProfileSettingsMenu'
    ).then((mod) => mod.ProfileSettingsMenuMobile),
  { ssr: false },
);

const ProfileSettingsMenuDesktop = dynamic(
  () =>
    import(
      /* webpackChunkName: "profileSettingsMenuDesktop" */ '@shikkhahub/shared/src/components/profile/ProfileSettingsMenu'
    ).then((mod) => mod.ProfileSettingsMenuDesktop),
  {
    ssr: false,
    loading: () => (
      <div className="h-[669px] w-64 rounded-16 border border-border-subtlest-tertiary" />
    ),
  },
);

export const navigationKey = generateQueryKey(
  RequestKey.AccountNavigation,
  null,
);

export default function SettingsLayout({
  children,
}: PropsWithChildren): ReactElement {
  const router = useRouter();
  const { user: profile, isAuthReady } = useContext(AuthContext);
  const isMobile = useViewSize(ViewSize.MobileL);
  const isLaptop = useViewSize(ViewSize.Laptop);
  const canPurchaseCores = useCanPurchaseCores();
  const [isOpen, setIsOpen] = useQueryState({
    key: navigationKey,
    defaultValue: false,
  });

  useEffect(() => {
    const onClose = () => setIsOpen(false);

    router.events.on('routeChangeComplete', onClose);

    return () => {
      router.events.off('routeChangeComplete', onClose);
    };
  }, [router.events, setIsOpen]);

  const { formRef } = useAuthForms();

  if (!isAuthReady) {
    return null;
  }

  if (!profile) {
    return (
      <div className="flex w-full items-center justify-center pt-10">
        <AuthOptions
          simplified
          isLoginFlow
          formRef={formRef}
          trigger={AuthTriggers.AccountPage}
        />
      </div>
    );
  }

  return (
    <>
      {!isMobile && !isLaptop && (
        <div className="hidden h-14 items-center gap-2 border-b border-border-subtlest-tertiary px-4 tablet:flex laptop:hidden">
          <Link href={webappUrl} passHref>
            <Button
              tag="a"
              variant={ButtonVariant.Tertiary}
              size={ButtonSize.XSmall}
              icon={<ArrowIcon className="-rotate-90" />}
            />
          </Link>

          <Typography bold tag={TypographyTag.H2} type={TypographyType.Body}>
            Settings
          </Typography>

          <BuyCreditsButton
            className="ml-auto"
            hideBuyButton={!canPurchaseCores}
            onPlusClick={() => {
              router.push(
                getPathnameWithQuery(
                  `${webappUrl}cores`,
                  new URLSearchParams({
                    origin: Origin.Settings,
                  }),
                ),
              );
            }}
          />
        </div>
      )}
      {router.query.redirectTo && router.query.redirectCopy && (
        <button
          type="button"
          onClick={() => router.push(router.query.redirectTo as string)}
          className="flex w-full items-center justify-center gap-2 border-b border-border-subtlest-tertiary bg-surface-float px-6 py-3 text-left transition-colors hover:bg-surface-hover"
        >
          <ArrowIcon className="-rotate-90 text-text-tertiary" />
          <Typography
            type={TypographyType.Callout}
            color={TypographyColor.Secondary}
          >
            {router.query.redirectCopy}
          </Typography>
        </button>
      )}
      <div className="mx-auto flex w-full max-w-5xl gap-4 tablet:p-6">
        <h1 className="sr-only">Settings</h1>
        {isMobile ? (
          <ProfileSettingsMenuMobile
            shouldKeepOpen
            isOpen={isOpen}
            onClose={() => router.push(profile.permalink)}
          />
        ) : (
          <ProfileSettingsMenuDesktop />
        )}
        {children}
      </div>
    </>
  );
}

export const getSettingsLayout = (page: ReactNode): ReactNode =>
  getFooterNavBarLayout(
    getMainLayout(<SettingsLayout>{page}</SettingsLayout>, null, {
      screenCentered: true,
      showSidebar: false,
    }),
  );
