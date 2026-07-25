import type { ReactElement } from 'react';
import React from 'react';
import {
  Button,
  ButtonSize,
  ButtonVariant,
} from '@shikkhahub/shared/src/components/buttons/Button';
import { PlusIcon } from '@shikkhahub/shared/src/components/icons';
import type { NextSeoProps } from 'next-seo';
import { UserExperienceType } from '@shikkhahub/shared/src/graphql/user/profile';
import { ExperienceSettings } from '@shikkhahub/shared/src/components/profile/ExperienceSettings';
import Link from '@shikkhahub/shared/src/components/utilities/Link';
import { webappUrl } from '@shikkhahub/shared/src/lib/constants';
import { getPageSeoTitles } from '../../../../components/layouts/utils';
import { defaultSeo } from '../../../../next-seo';
import { getSettingsLayout } from '../../../../components/layouts/SettingsLayout';
import { AccountPageContainer } from '../../../../components/layouts/SettingsLayout/AccountPageContainer';

const seo: NextSeoProps = {
  ...defaultSeo,
  ...getPageSeoTitles('Work Experience'),
};

const WorkExperiencePage = (): ReactElement => {
  return (
    <AccountPageContainer
      title="Work Experience"
      actions={
        <Link
          href={`${webappUrl}settings/profile/experience/edit?type=${UserExperienceType.Work}`}
        >
          <Button
            variant={ButtonVariant.Subtle}
            size={ButtonSize.Small}
            icon={<PlusIcon />}
          >
            Add
          </Button>
        </Link>
      }
    >
      <ExperienceSettings
        experienceType={UserExperienceType.Work}
        emptyStateMessage="No work experience added yet"
      />
    </AccountPageContainer>
  );
};

WorkExperiencePage.getLayout = getSettingsLayout;
WorkExperiencePage.layoutProps = { seo };

export default WorkExperiencePage;
