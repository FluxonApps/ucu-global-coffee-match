import { getDownloadURL, ref, uploadBytes } from 'firebase/storage';
import { Camera, Check, Link as LinkIcon, LogOut, Unlink, User } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { useNavigate } from 'react-router';

import AvailabilityCalendar from '../components/ui/AvailabilityCalendar.tsx';
import Btn from '../components/ui/Btn.tsx';
import Card from '../components/ui/Card.tsx';
import { FormInput, MultiSelect } from '../components/ui/FormInput.tsx';
import { useAuth } from '../context/useAuth.ts';
import { useProfileDetails } from '../context/useProfileDetails.ts';
import {
  INTEREST_OPTIONS,
  LANGUAGE_OPTIONS,
  SKILL_OPTIONS,
  TIMEZONE_OPTIONS,
  TOPIC_OPTIONS,
} from '../data/options.ts';
import { ApiError } from '../lib/api.ts';
import { storage } from '../lib/firebase.ts';
import type { ProfileDetails } from '../types/coffeeMatch.ts';

type MultiField =
  | 'skills'
  | 'interests'
  | 'languages'
  | 'topics'
  | 'format';

const ProfilePage = () => {
  const { user, logout, updateProfile } = useAuth();
  const { details, setDetails } = useProfileDetails();
  const navigate = useNavigate();

  const [firstName, setFirstName] = useState(user?.first_name ?? '');
  const [lastName, setLastName] = useState(user?.last_name ?? '');
  const [timezone, setTimezone] = useState(user?.timezone ?? '');

  const [local, setLocal] = useState<ProfileDetails>(details);
  const [photoPreview, setPhotoPreview] = useState(details.photoUrl);
  const [slackInput, setSlackInput] = useState(details.slackHandle);

  const fileRef = useRef<HTMLInputElement>(null);

  const [saved, setSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSigningOut, setIsSigningOut] = useState(false);

  useEffect(() => {
    setFirstName(user?.first_name ?? '');
    setLastName(user?.last_name ?? '');
    setTimezone(user?.timezone ?? '');
  }, [user]);

  useEffect(() => {
    setLocal(details);
    setPhotoPreview(details.photoUrl);
    setSlackInput(details.slackHandle);
  }, [details]);

  const set =
    (key: keyof ProfileDetails) =>
    (value: string) => {
      setLocal((current) => ({
        ...current,
        [key]: value,
      }));
    };

  const toggle =
    (key: MultiField) =>
    (value: string) => {
      setLocal((current) => ({
        ...current,
        [key]: current[key].includes(value)
          ? current[key].filter((item) => item !== value)
          : [...current[key], value],
      }));
    };

  const toggleSlot = (slot: string) => {
    setLocal((current) => ({
      ...current,
      availability: current.availability.includes(slot)
        ? current.availability.filter((item) => item !== slot)
        : [...current.availability, slot],
    }));
  };

  const handlePhoto = async (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];

    if (!file || !user) {
      return;
    }

    if (!file.type.startsWith('image/')) {
      setError('Please select an image.');
      event.target.value = '';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('The image must be smaller than 5 MB.');
      event.target.value = '';
      return;
    }

    setError(null);
    setIsUploadingPhoto(true);

    try {
      const safeFileName = file.name.replace(
        /[^a-zA-Z0-9.-]/g,
        '_',
      );

      const photoReference = ref(
        storage,
        `avatars/${user.id}/${Date.now()}-${safeFileName}`,
      );

      await uploadBytes(photoReference, file, {
        contentType: file.type,
      });

      const photoUrl = await getDownloadURL(photoReference);

      setPhotoPreview(photoUrl);

      setLocal((current) => ({
        ...current,
        photoUrl,
      }));
    } catch (uploadError) {
      console.error(uploadError);
      setError('Failed to upload photo. Please try again.');
    } finally {
      setIsUploadingPhoto(false);
      event.target.value = '';
    }
  };

  const connectSlack = () => {
    if (!slackInput.trim()) {
      return;
    }

    setLocal((current) => ({
      ...current,
      slackConnected: true,
      slackHandle: slackInput.trim(),
    }));
  };

  const disconnectSlack = () => {
    setLocal((current) => ({
      ...current,
      slackConnected: false,
      slackHandle: '',
    }));

    setSlackInput('');
  };

  const saveAll = async () => {
    setError(null);
    setIsSaving(true);

    try {
      await updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        timezone,
      });

      setDetails(local);

      setSaved(true);

      window.setTimeout(() => {
        setSaved(false);
      }, 2000);
    } catch (saveError) {
      setError(
        saveError instanceof ApiError
          ? saveError.message
          : 'Failed to save profile. Please, try again.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleSignOut = async () => {
    setIsSigningOut(true);

    try {
      await logout();
      void navigate('/');
    } finally {
      setIsSigningOut(false);
    }
  };

  if (!user) {
    return null;
  }

  const displayedName =
    `${firstName} ${lastName}`.trim() || 'Your Name';

  const saveButtonLabel = saved ? (
    <>
      <Check size={14} />
      Saved!
    </>
  ) : isSaving ? (
    'Saving…'
  ) : (
    'Save Changes'
  );

  return (
    <div className="min-h-screen bg-background pt-14">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-medium font-display">
              Your Profile
            </h1>

            <p className="text-sm text-muted-foreground mt-0.5">
              This is how colleagues see you on Coffee Match.
            </p>
          </div>

          <Btn
            variant="primary"
            size="sm"
            onClick={saveAll}
            disabled={isSaving || isUploadingPhoto}
          >
            {saveButtonLabel}
          </Btn>
        </div>

        {error && (
          <p className="text-sm text-destructive mb-4">
            {error}
          </p>
        )}

        <Card className="p-6 mb-4">
          <h2 className="font-semibold mb-4 font-display">
            Photo & Basics
          </h2>

          <div className="flex items-start gap-5 mb-5">
            <div className="relative group flex-shrink-0">
              {photoPreview ? (
                <img
                  src={photoPreview}
                  alt={`${displayedName} profile`}
                  className="w-20 h-20 rounded-full object-cover bg-muted"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center border-2 border-dashed border-border">
                  <User
                    size={28}
                    className="text-muted-foreground"
                  />
                </div>
              )}

              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                disabled={isUploadingPhoto}
                aria-label="Upload profile photo"
                className="absolute inset-0 rounded-full bg-foreground/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center disabled:cursor-not-allowed"
              >
                <Camera size={18} className="text-white" />
              </button>

              <input
                ref={fileRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handlePhoto}
              />
            </div>

            <div className="flex-1">
              <p className="text-sm font-semibold text-foreground">
                {displayedName}
              </p>

              <p className="text-xs text-muted-foreground mb-3">
                {user.email}
              </p>

              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                disabled={isUploadingPhoto}
                className="text-xs text-primary font-medium hover:underline flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Camera size={12} />

                {isUploadingPhoto
                  ? 'Uploading…'
                  : photoPreview
                    ? 'Change photo'
                    : 'Upload photo'}
              </button>

              <p className="text-xs text-muted-foreground mt-1">
                Shown to colleagues on your match cards.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormInput
              label="First name"
              value={firstName}
              onChange={setFirstName}
              placeholder="Alex"
            />

            <FormInput
              label="Last name"
              value={lastName}
              onChange={setLastName}
              placeholder="Chen"
            />

            <div className="col-span-2">
              <FormInput
                label="Timezone"
                value={timezone}
                onChange={setTimezone}
                options={TIMEZONE_OPTIONS}
              />
            </div>

            <div className="col-span-2">
              <FormInput
                label="Bio"
                type="textarea"
                value={local.bio}
                onChange={set('bio')}
                placeholder="Tell colleagues a little about yourself — what you're working on, what you enjoy, what you're curious about."
              />

              <p className="text-xs text-muted-foreground mt-1">
                Not saved to the server yet — kept on this
                device only.
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6 mb-4">
          <h2 className="font-semibold mb-1 font-display">
            Slack
          </h2>

          <p className="text-sm text-muted-foreground mb-4">
            Connect your Slack handle so matches can reach you
            directly.
          </p>

          {local.slackConnected ? (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-primary/5 border border-primary/20">
              <div className="w-8 h-8 rounded-lg bg-[#4A154B] flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
                #
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">
                  Connected
                </p>

                <p className="text-xs text-muted-foreground">
                  @{local.slackHandle}
                </p>
              </div>

              <Btn
                variant="ghost"
                size="sm"
                onClick={disconnectSlack}
              >
                <Unlink size={13} />
                Disconnect
              </Btn>
            </div>
          ) : (
            <div className="flex gap-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                  @
                </span>

                <input
                  type="text"
                  value={slackInput}
                  onChange={(event) =>
                    setSlackInput(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      connectSlack();
                    }
                  }}
                  placeholder="your-slack-handle"
                  className="w-full rounded-xl border border-border bg-input-background pl-7 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
                />
              </div>

              <Btn
                variant="secondary"
                size="md"
                onClick={connectSlack}
              >
                <LinkIcon size={13} />
                Connect
              </Btn>
            </div>
          )}
        </Card>

        <Card className="p-6 mb-4">
          <h2 className="font-semibold mb-1 font-display">
            Interests & Topics
          </h2>

          <p className="text-xs text-muted-foreground mb-4">
            Used to find your best matches. Select everything
            that resonates.
          </p>

          <div className="flex flex-col gap-5">
            <MultiSelect
              label="Personal Interests"
              options={INTEREST_OPTIONS}
              selected={local.interests}
              onToggle={toggle('interests')}
              hint="Pick as many as you like."
            />

            <MultiSelect
              label="Conversation Topics"
              options={TOPIC_OPTIONS}
              selected={local.topics}
              onToggle={toggle('topics')}
              hint="What do you enjoy discussing at work?"
            />
          </div>
        </Card>

        <Card className="p-6 mb-4">
          <h2 className="font-semibold mb-1 font-display">
            Skills & Languages
          </h2>

          <p className="text-xs text-muted-foreground mb-4">
            Helps colleagues understand your background before
            you meet.
          </p>

          <div className="flex flex-col gap-5">
            <MultiSelect
              label="Skills"
              options={SKILL_OPTIONS}
              selected={local.skills}
              onToggle={toggle('skills')}
            />

            <MultiSelect
              label="Languages"
              options={LANGUAGE_OPTIONS}
              selected={local.languages}
              onToggle={toggle('languages')}
            />
          </div>
        </Card>

        <Card className="p-6 mb-4">
          <h2 className="font-semibold mb-1 font-display">
            Availability
          </h2>

          <p className="text-xs text-muted-foreground mb-5">
            Click or drag to mark the hours when you're usually
            free for a coffee chat. All times are in your local
            timezone.
          </p>

          <AvailabilityCalendar
            selected={local.availability}
            onToggle={toggleSlot}
          />
        </Card>

        <div className="flex justify-between items-center pb-8">
          <Btn
            variant="ghost"
            size="sm"
            onClick={handleSignOut}
            disabled={isSigningOut}
          >
            <LogOut size={14} />
            Sign Out
          </Btn>

          <Btn
            variant="primary"
            size="md"
            onClick={saveAll}
            disabled={isSaving || isUploadingPhoto}
          >
            {saveButtonLabel}
          </Btn>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
