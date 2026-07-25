import type { ReactNode } from 'react';
import React from 'react';
import type { MainLayoutProps } from '@shikkhahub/shared/src/components/MainLayout';

import { NoSidebarLayout } from '@shikkhahub/shared/src/components/NoSidebarLayout';
import { getLayout as getMainLayout } from './MainLayout';

export const getLayout = (
  page: ReactNode,
  pageProps: Record<string, unknown>,
  layoutProps: MainLayoutProps,
): ReactNode =>
  getMainLayout(
    <NoSidebarLayout hideBackButton={layoutProps?.hideBackButton}>
      {page}
    </NoSidebarLayout>,
    pageProps,
    {
      ...layoutProps,
      showSidebar: false,
    },
  );
