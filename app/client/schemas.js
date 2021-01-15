import { schema } from "normalizr";

const user = new schema.Entity("users");

const credit_sends = new schema.Entity("credit_sends", {
  sender_user: user,
  recipient_user: user
});
const credit_receives = new schema.Entity("credit_receives", {
  sender_user: user,
  recipient_user: user
});

const transfer_account = new schema.Entity("transfer_accounts", {
  users: [user],
  credit_sends: [credit_sends],
  credit_receives: [credit_receives]
});

const credit_transfer = new schema.Entity("credit_transfers", {
  sender_transfer_account: transfer_account,
  sender_user: user,
  recipient_transfer_account: transfer_account,
  recipient_user: user
});

const token = new schema.Entity("tokens");

const filter = new schema.Entity("filters");

const admin = new schema.Entity("admins");

const invite = new schema.Entity("invites");

const organisation = new schema.Entity("organisations", {
  token: token
});

export const transferAccountSchema = [transfer_account];

export const creditTransferSchema = [credit_transfer];

export const userSchema = [user];

export const tokenSchema = [token];

export const filterSchema = [filter];

export const adminUserSchema = [admin];

export const inviteUserSchema = [invite];

export const organisationSchema = [organisation];
