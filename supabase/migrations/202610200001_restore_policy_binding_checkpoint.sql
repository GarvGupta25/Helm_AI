-- Member consent still dispatches quotation requests directly. Policy binding
-- requires the separate human review completed after provider acceptance.
CREATE OR REPLACE FUNCTION public.enforce_marketplace_policy_checkpoint()
RETURNS trigger
LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.marketplace_applications application
        JOIN public.provider_quotations quotation
          ON quotation.id = NEW.quotation_id AND quotation.application_id = application.id
        WHERE application.id = NEW.application_id
          AND application.owner_id = NEW.owner_id
          AND application.provider_id = NEW.provider_id
          AND quotation.provider_id = NEW.provider_id
          AND application.status = 'broker_final_review'
          AND quotation.status = 'accepted'
    ) OR NOT EXISTS (
        SELECT 1 FROM public.review_decisions review
        WHERE review.marketplace_application_id = NEW.application_id
          AND review.checkpoint = 'checkpoint_2' AND review.action = 'approve'
    ) THEN
        RAISE EXCEPTION 'accepted quotation and checkpoint 2 approval are required before policy creation';
    END IF;
    RETURN NEW;
END;
$$;

-- Match direct Supabase reads to the API's assigned-broker scope.
CREATE FUNCTION public.marketplace_can_review(member_id text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT COALESCE(auth.jwt() -> 'app_metadata' ->> 'helm_role' = 'broker', false)
       AND EXISTS (
           SELECT 1 FROM public.broker_assignments assignment
           WHERE assignment.member_id = $1
             AND assignment.broker_id = auth.uid()::text
       );
$$;
REVOKE ALL ON FUNCTION public.marketplace_can_review(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.marketplace_can_review(text) TO authenticated;

ALTER POLICY marketplace_applications_scoped_read ON public.marketplace_applications
USING (owner_id = auth.uid()::text OR provider_id = public.current_provider_id()
       OR public.marketplace_can_review(owner_id));
ALTER POLICY provider_quotations_scoped_read ON public.provider_quotations
USING (provider_id = public.current_provider_id() OR EXISTS (
    SELECT 1 FROM public.marketplace_applications application
    WHERE application.id = provider_quotations.application_id
      AND (application.owner_id = auth.uid()::text OR public.marketplace_can_review(application.owner_id))
));
ALTER POLICY policies_marketplace_scoped_read ON public.policies_marketplace
USING (owner_id = auth.uid()::text OR provider_id = public.current_provider_id()
       OR public.marketplace_can_review(owner_id));
ALTER POLICY provider_payments_scoped_read ON public.provider_payments
USING (owner_id = auth.uid()::text OR public.marketplace_can_review(owner_id) OR EXISTS (
    SELECT 1 FROM public.policies_marketplace policy
    WHERE policy.id = provider_payments.policy_id AND policy.provider_id = public.current_provider_id()
));
ALTER POLICY provider_flags_scoped_read ON public.provider_flags
USING (owner_id = auth.uid()::text OR provider_id = public.current_provider_id()
       OR public.marketplace_can_review(owner_id));
