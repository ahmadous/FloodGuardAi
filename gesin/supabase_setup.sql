-- ══════════════════════════════════════════════════════════════════════════
-- GESIN — Setup Supabase pour les signalements d'inondation
-- À exécuter dans : https://supabase.com → SQL Editor
-- ══════════════════════════════════════════════════════════════════════════

-- 1. TABLE : signalements
-- ──────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.signalements (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  timestamptz NOT NULL DEFAULT now(),

    -- Contenu du signalement
    description text NOT NULL,
    severity    text NOT NULL CHECK (severity IN ('faible', 'modéré', 'élevé', 'critique')),
    status      text NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'analysis', 'validated', 'rejected')),

    -- Photo
    photo_url   text,
    photo_path  text,

    -- Géolocalisation
    latitude    double precision,
    longitude   double precision,

    -- Métadonnées
    people_impacted integer,
    source      text DEFAULT 'mobile_gesin',
    notes       text       -- notes admin
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_signalements_severity  ON public.signalements (severity);
CREATE INDEX IF NOT EXISTS idx_signalements_status    ON public.signalements (status);
CREATE INDEX IF NOT EXISTS idx_signalements_created   ON public.signalements (created_at DESC);

-- RLS : tout le monde peut INSERT (signalement citoyen), seuls les admins lisent
ALTER TABLE public.signalements ENABLE ROW LEVEL SECURITY;

-- Politique : insertion publique (app mobile sans auth)
CREATE POLICY "Citoyens peuvent signaler"
    ON public.signalements
    FOR INSERT
    WITH CHECK (true);

-- Politique : lecture pour les utilisateurs authentifiés (admin web)
CREATE POLICY "Admins peuvent lire"
    ON public.signalements
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Politique : update/delete pour les admins
CREATE POLICY "Admins peuvent modifier"
    ON public.signalements
    FOR ALL
    USING (auth.role() = 'authenticated');


-- 2. BUCKET STORAGE : flood-reports
-- ──────────────────────────────────────────────────────────────────────────
-- À faire dans : Supabase → Storage → New Bucket
--   Nom    : flood-reports
--   Public : OUI (pour que les photo_url soient accessibles)

-- Ou via SQL (nécessite droits storage) :
INSERT INTO storage.buckets (id, name, public)
VALUES ('flood-reports', 'flood-reports', true)
ON CONFLICT (id) DO NOTHING;

-- Politique storage : upload public (sans auth)
CREATE POLICY "Upload public signalements"
    ON storage.objects
    FOR INSERT
    WITH CHECK (bucket_id = 'flood-reports');

-- Politique storage : lecture publique des photos
CREATE POLICY "Lecture publique photos"
    ON storage.objects
    FOR SELECT
    USING (bucket_id = 'flood-reports');
