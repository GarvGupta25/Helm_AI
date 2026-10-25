import { Link } from 'react-router-dom';
import type { Profile } from '../api';
import { DetailRow } from './Checkout';
import { formatDate, hospitalName, readable, wholeMoney } from './checkoutPresentation';
import { pathFor } from './steps';

export function ProfileSummary({ profile }: { profile: Profile }) {
  const noBenefits = profile.benefits.required?.length === 0 && profile.benefits.preferred.length === 0;
  return <div className="flow-profile"><dl className="flow-details">
    <DetailRow label="Who needs cover" edit="people" editLabel="Edit people">{profile.people.map((person, index) => <span className="flow-person" key={index}>{person.relationship === 'child' ? 'Child' : person.relationship === 'partner' ? 'Partner' : 'Adult'}{person.age_years !== null ? `, age ${person.age_years}` : person.date_of_birth ? `, born ${formatDate(person.date_of_birth)}` : ', age missing'}</span>)}</DetailRow>
    <DetailRow label="Location" edit="region" editLabel="Edit location">{profile.location.region || 'Not answered'}</DetailRow>
    <DetailRow label="Cover starts" edit="start-date" editLabel="Edit start date">{formatDate(profile.cover.start_date)}</DetailRow>
    <DetailRow label="Budget" edit="budget" editLabel="Edit budget">{profile.budget.choice === 'no_target' ? 'No limit set' : profile.budget.monthly_pence !== null ? `${wholeMoney(profile.budget.monthly_pence)} a month` : 'Not answered'}{profile.budget.strict ? ' (maximum)' : ''}</DetailRow>
    <DetailRow label="Excess" edit="excess" editLabel="Edit excess">{profile.excess.choice === 'no_preference' ? 'No preference' : profile.excess.max_pence !== null ? wholeMoney(profile.excess.max_pence) : 'Not answered'}{profile.excess.strict ? ' (maximum)' : ''}</DetailRow>
    <DetailRow label="Hospital list" edit="hospitals" editLabel="Edit hospital list">{hospitalName(profile.hospital_list.minimum_tier)}</DetailRow>
    {!noBenefits && <><DetailRow label="Essential benefits" edit="benefits/hospital" editLabel="Edit benefits">{profile.benefits.required === null ? 'Not reviewed' : profile.benefits.required.map(readable).join(', ') || 'None selected'}</DetailRow><DetailRow label="Preferred benefits" edit="benefits/hospital" editLabel="Edit preferred benefits">{profile.benefits.preferred.map(readable).join(', ') || 'None selected'}</DetailRow></>}
  </dl>{noBenefits && <details className="flow-empty-options"><summary>Optional (none added)</summary><p>Essential benefits: none selected. Preferred benefits: none selected.</p><Link to={pathFor('benefits/hospital') + '?return=review'}>Edit benefits</Link></details>}</div>;
}
