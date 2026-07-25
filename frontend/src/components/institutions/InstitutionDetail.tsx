import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MapPin, Phone, Mail, Globe, Building2, Calendar, CheckCircle, AlertCircle } from 'lucide-react';
import { useInstitution, useRecentlyViewed } from '../../hooks';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import { Button } from '../common/Button';
import { Skeleton } from '../Skeleton';

export function InstitutionDetail() {
  const { slug } = useParams<{ slug: string }>();
  const { institution, loading, error } = useInstitution(slug || '');
  const { addToRecentlyViewed } = useRecentlyViewed();

  // Track view when institution loads
  useEffect(() => {
    if (institution) {
      addToRecentlyViewed(institution);
    }
  }, [institution, addToRecentlyViewed]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error || !institution) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto text-red-500" />
        <h2 className="mt-4 text-xl font-semibold">Institution not found</h2>
        <p className="mt-2 text-muted-foreground">
          {error?.message || 'The institution you are looking for does not exist.'}
        </p>
      </div>
    );
  }

  const { name_en, name_bn, short_name, description, type, established_year, address, phone, email, website, upazila, verification_status, is_featured } = institution;

  const locationParts = [address, upazila?.name_en, upazila?.district?.name_en, upazila?.district?.division?.name_en].filter(Boolean);
  const fullLocation = locationParts.join(', ');

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                {is_featured && (
                  <span className="px-2.5 py-1 bg-primary/10 text-primary text-sm rounded-full font-medium">
                    Featured
                  </span>
                )}
                {verification_status === 'verified' && (
                  <span className="flex items-center gap-1 px-2.5 py-1 bg-green-100 text-green-700 text-sm rounded-full">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Verified
                  </span>
                )}
                {type?.name && (
                  <span className="px-2.5 py-1 bg-secondary text-muted-foreground text-sm rounded-full">
                    {type.name}
                  </span>
                )}
              </div>
              
              <h1 className="mt-3 text-3xl font-bold text-foreground">{name_en}</h1>
              {short_name && short_name !== name_en && (
                <p className="text-lg text-muted-foreground">{short_name}</p>
              )}
              {name_bn && <p className="text-lg text-muted-foreground font-bangla">{name_bn}</p>}
            </div>

            <div className="flex gap-2">
              <Button variant="outline">Compare</Button>
              <Button variant="primary">Contact</Button>
            </div>
          </div>

          {/* Quick Info */}
          <div className="flex flex-wrap gap-6 mt-6 pt-6 border-t border-border">
            {established_year && (
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Established</span>
                <span className="font-medium">{established_year}</span>
              </div>
            )}
            {fullLocation && (
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Location</span>
                <span className="font-medium">{fullLocation}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Description */}
      {description && (
        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-foreground leading-relaxed">{description}</p>
          </CardContent>
        </Card>
      )}

      {/* Contact Info */}
      <Card>
        <CardHeader>
          <CardTitle>Contact Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 gap-4">
            {phone && (
              <a href={`tel:${phone}`} className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary transition-colors">
                <Phone className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Phone</p>
                  <p className="font-medium">{phone}</p>
                </div>
              </a>
            )}
            {email && (
              <a href={`mailto:${email}`} className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary transition-colors">
                <Mail className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{email}</p>
                </div>
              </a>
            )}
            {website && (
              <a href={website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary transition-colors">
                <Globe className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Website</p>
                  <p className="font-medium">{website.replace(/^https?:\/\//, '')}</p>
                </div>
              </a>
            )}
            {fullLocation && (
              <div className="flex items-center gap-3 p-3 rounded-lg">
                <Building2 className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Address</p>
                  <p className="font-medium">{fullLocation}</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
