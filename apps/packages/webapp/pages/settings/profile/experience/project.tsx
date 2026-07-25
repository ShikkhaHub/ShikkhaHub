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
  ...getPageSeoTitles('Projects & Publications'),
};

const ProjectsPage = (): ReactElement => {
  return (
    <AccountPageContainer
      title="Projects & Publications"
      actions={
        <Link
          href={`${webappUrl}settings/profile/experience/edit?type=${UserExperienceType.Project}`}
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
        experienceType={UserExperienceType.Project}
        emptyStateMessage="No projects added yet"
      />
    </AccountPageContainer>
  );
};

ProjectsPage.getLayout = getSettingsLayout;
ProjectsPage.layoutProps = { seo };

export default ProjectsPage;
