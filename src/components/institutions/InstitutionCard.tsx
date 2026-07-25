import { Link } from 'react-router-dom';
import { MapPin, Building2, ExternalLink } from 'lucide-react';
import { Card, CardContent } from '../common/Card';
import { CompareButton } from '../CompareButton';
import type { Institution } from '../../types';

interface InstitutionCardProps {
  institution: Institution;
  showActions?: boolean;
}

export function InstitutionCard({ institution, showActions = true }: InstitutionCardProps) {
  const { name_en, short_name, slug, type, address, upazila, is_featured } = institution;

  const locationParts = [upazila?.name_en, upazila?.district?.name_en].filter(Boolean);
  const location = locationParts.length > 0 ? locationParts.join(', ') : address || 'Bangladesh';

  return (
    <Card hover className="overflow-hidden">
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {is_featured && (
                <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full font-medium">
                  Featured
                </span>
              )}
              {type?.name && (
                <span className="px-2 py-0.5 bg-secondary text-muted-foreground text-xs rounded-full">
                  {type.name}
                </span>
              )}
            </div>
            
            <Link
              to={`/institutions/${slug}`}
              className="block mt-2 group"
            >
              <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                {name_en}
              </h3>
              {short_name && short_name !== name_en && (
                <p className="text-sm text-muted-foreground truncate">{short_name}</p>
              )}
            </Link>
          </div>
          
          {showActions && (
            <CompareButton institutionId={institution.id} />
          )}
        </div>

        {/* Location */}
        {location && (
          <div className="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
            <MapPin className="h-4 w-4 shrink-0" />
            <span className="truncate">{location}</span>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4" />
            <span>Est. {institution.established_year || 'N/A'}</span>
          </div>
          
          <Link
            to={`/institutions/${slug}`}
            className="flex items-center gap-1 text-sm text-primary hover:text-primary-hover font-medium"
          >
            View Details
            <ExternalLink className="h-4 w-4" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
