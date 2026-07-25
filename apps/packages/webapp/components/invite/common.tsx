import type { ReferralCampaignKey } from '@shikkhahub/shared/src/hooks';
import type { Author } from '@shikkhahub/shared/src/graphql/comments';
import Logo, { LogoPosition } from '@shikkhahub/shared/src/components/Logo';
import type { ReactElement } from 'react';
import React from 'react';

export interface JoinPageProps {
  token?: string;
  redirectTo?: string;
  referringUser: Author;
  campaign: ReferralCampaignKey;
}

export const DailyDevLogo = (): ReactElement => {
  return (
    <span className="absolute left-1/2 top-8 -translate-x-1/2 laptop:left-12 laptop:translate-x-0">
      <Logo position={LogoPosition.Relative} />
    </span>
  );
};
