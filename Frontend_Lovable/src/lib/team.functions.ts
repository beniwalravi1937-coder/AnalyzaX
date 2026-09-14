import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";

const tokenSchema = z.object({ token: z.string().min(6) });

export interface InvitationDetails {
  status: "valid" | "expired" | "accepted" | "revoked" | "invalid";
  id?: string;
  email?: string;
  role?: string;
  workspaceName?: string;
  invitedByName?: string | null;
}

/** Public: look up an invitation by its token (no session required). */
export const verifyInvitation = createServerFn({ method: "GET" })
  .inputValidator((data: unknown) => tokenSchema.parse(data))
  .handler(async ({ data }): Promise<InvitationDetails> => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { data: row } = await supabaseAdmin
      .from("team_invitations")
      .select("id, email, role, workspace_name, invited_by, accepted_at, revoked_at, expires_at")
      .eq("token", data.token)
      .maybeSingle();

    if (!row) return { status: "invalid" };

    let invitedByName: string | null = null;
    const { data: inviter } = await supabaseAdmin
      .from("profiles")
      .select("display_name, email")
      .eq("id", row.invited_by)
      .maybeSingle();
    if (inviter) invitedByName = inviter.display_name ?? inviter.email ?? null;

    const base = {
      id: row.id,
      email: row.email,
      role: row.role,
      workspaceName: row.workspace_name,
      invitedByName,
    };

    if (row.revoked_at) return { status: "revoked", ...base };
    if (row.accepted_at) return { status: "accepted", ...base };
    if (new Date(row.expires_at).getTime() < Date.now()) return { status: "expired", ...base };
    return { status: "valid", ...base };
  });

/** Accept an invitation as the signed-in user. */
export const acceptInvitation = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((data: unknown) => tokenSchema.parse(data))
  .handler(async ({ data, context }) => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { data: row } = await supabaseAdmin
      .from("team_invitations")
      .select("id, accepted_at, revoked_at, expires_at, workspace_name")
      .eq("token", data.token)
      .maybeSingle();

    if (!row) throw new Error("This invitation link is not valid.");
    if (row.revoked_at) throw new Error("This invitation was cancelled.");
    if (row.accepted_at) throw new Error("This invitation has already been used.");
    if (new Date(row.expires_at).getTime() < Date.now()) throw new Error("This invitation has expired.");

    const { error } = await supabaseAdmin
      .from("team_invitations")
      .update({ accepted_at: new Date().toISOString(), accepted_by: context.userId })
      .eq("id", row.id);
    if (error) throw new Error(error.message);

    return { ok: true, workspaceName: row.workspace_name };
  });

const createSchema = z.object({
  email: z.string().email(),
  role: z.string().min(1).max(40),
  workspaceName: z.string().min(1).max(80).optional(),
});

export const createInvitation = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((data: unknown) => createSchema.parse(data))
  .handler(async ({ data, context }) => {
    const { data: row, error } = await context.supabase
      .from("team_invitations")
      .insert({
        email: data.email.toLowerCase(),
        role: data.role,
        workspace_name: data.workspaceName ?? "AnalyzaX Workspace",
        invited_by: context.userId,
      })
      .select("id, token, email, role, expires_at, created_at")
      .single();
    if (error) throw new Error(error.message);
    return row;
  });

export const listInvitations = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { data, error } = await context.supabase
      .from("team_invitations")
      .select("id, token, email, role, accepted_at, revoked_at, expires_at, created_at")
      .order("created_at", { ascending: false });
    if (error) throw new Error(error.message);
    return data ?? [];
  });

export const revokeInvitation = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((data: unknown) => z.object({ id: z.string().uuid() }).parse(data))
  .handler(async ({ data, context }) => {
    const { error } = await context.supabase
      .from("team_invitations")
      .update({ revoked_at: new Date().toISOString() })
      .eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true };
  });
