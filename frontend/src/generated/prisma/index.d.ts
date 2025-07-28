
/**
 * Client
**/

import * as runtime from './runtime/library.js';
import $Types = runtime.Types // general types
import $Public = runtime.Types.Public
import $Utils = runtime.Types.Utils
import $Extensions = runtime.Types.Extensions
import $Result = runtime.Types.Result

export type PrismaPromise<T> = $Public.PrismaPromise<T>


/**
 * Model Account
 * 
 */
export type Account = $Result.DefaultSelection<Prisma.$AccountPayload>
/**
 * Model Session
 * 
 */
export type Session = $Result.DefaultSelection<Prisma.$SessionPayload>
/**
 * Model User
 * 
 */
export type User = $Result.DefaultSelection<Prisma.$UserPayload>
/**
 * Model VerificationToken
 * 
 */
export type VerificationToken = $Result.DefaultSelection<Prisma.$VerificationTokenPayload>
/**
 * Model EmailVerificationRequest
 * 
 */
export type EmailVerificationRequest = $Result.DefaultSelection<Prisma.$EmailVerificationRequestPayload>
/**
 * Model LocalUserProfile
 * 
 */
export type LocalUserProfile = $Result.DefaultSelection<Prisma.$LocalUserProfilePayload>
/**
 * Model LocalArticle
 * 
 */
export type LocalArticle = $Result.DefaultSelection<Prisma.$LocalArticlePayload>
/**
 * Model FeedSync
 * 
 */
export type FeedSync = $Result.DefaultSelection<Prisma.$FeedSyncPayload>
/**
 * Model FeedItem
 * 
 */
export type FeedItem = $Result.DefaultSelection<Prisma.$FeedItemPayload>
/**
 * Model SyncJob
 * 
 */
export type SyncJob = $Result.DefaultSelection<Prisma.$SyncJobPayload>

/**
 * ##  Prisma Client ʲˢ
 *
 * Type-safe database client for TypeScript & Node.js
 * @example
 * ```
 * const prisma = new PrismaClient()
 * // Fetch zero or more Accounts
 * const accounts = await prisma.account.findMany()
 * ```
 *
 *
 * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
 */
export class PrismaClient<
  ClientOptions extends Prisma.PrismaClientOptions = Prisma.PrismaClientOptions,
  U = 'log' extends keyof ClientOptions ? ClientOptions['log'] extends Array<Prisma.LogLevel | Prisma.LogDefinition> ? Prisma.GetEvents<ClientOptions['log']> : never : never,
  ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs
> {
  [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['other'] }

    /**
   * ##  Prisma Client ʲˢ
   *
   * Type-safe database client for TypeScript & Node.js
   * @example
   * ```
   * const prisma = new PrismaClient()
   * // Fetch zero or more Accounts
   * const accounts = await prisma.account.findMany()
   * ```
   *
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client).
   */

  constructor(optionsArg ?: Prisma.Subset<ClientOptions, Prisma.PrismaClientOptions>);
  $on<V extends U>(eventType: V, callback: (event: V extends 'query' ? Prisma.QueryEvent : Prisma.LogEvent) => void): PrismaClient;

  /**
   * Connect with the database
   */
  $connect(): $Utils.JsPromise<void>;

  /**
   * Disconnect from the database
   */
  $disconnect(): $Utils.JsPromise<void>;

  /**
   * Add a middleware
   * @deprecated since 4.16.0. For new code, prefer client extensions instead.
   * @see https://pris.ly/d/extensions
   */
  $use(cb: Prisma.Middleware): void

/**
   * Executes a prepared raw query and returns the number of affected rows.
   * @example
   * ```
   * const result = await prisma.$executeRaw`UPDATE User SET cool = ${true} WHERE email = ${'user@email.com'};`
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Executes a raw query and returns the number of affected rows.
   * Susceptible to SQL injections, see documentation.
   * @example
   * ```
   * const result = await prisma.$executeRawUnsafe('UPDATE User SET cool = $1 WHERE email = $2 ;', true, 'user@email.com')
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $executeRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<number>;

  /**
   * Performs a prepared raw query and returns the `SELECT` data.
   * @example
   * ```
   * const result = await prisma.$queryRaw`SELECT * FROM User WHERE id = ${1} OR email = ${'user@email.com'};`
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRaw<T = unknown>(query: TemplateStringsArray | Prisma.Sql, ...values: any[]): Prisma.PrismaPromise<T>;

  /**
   * Performs a raw query and returns the `SELECT` data.
   * Susceptible to SQL injections, see documentation.
   * @example
   * ```
   * const result = await prisma.$queryRawUnsafe('SELECT * FROM User WHERE id = $1 OR email = $2;', 1, 'user@email.com')
   * ```
   *
   * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/raw-database-access).
   */
  $queryRawUnsafe<T = unknown>(query: string, ...values: any[]): Prisma.PrismaPromise<T>;


  /**
   * Allows the running of a sequence of read/write operations that are guaranteed to either succeed or fail as a whole.
   * @example
   * ```
   * const [george, bob, alice] = await prisma.$transaction([
   *   prisma.user.create({ data: { name: 'George' } }),
   *   prisma.user.create({ data: { name: 'Bob' } }),
   *   prisma.user.create({ data: { name: 'Alice' } }),
   * ])
   * ```
   * 
   * Read more in our [docs](https://www.prisma.io/docs/concepts/components/prisma-client/transactions).
   */
  $transaction<P extends Prisma.PrismaPromise<any>[]>(arg: [...P], options?: { isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<runtime.Types.Utils.UnwrapTuple<P>>

  $transaction<R>(fn: (prisma: Omit<PrismaClient, runtime.ITXClientDenyList>) => $Utils.JsPromise<R>, options?: { maxWait?: number, timeout?: number, isolationLevel?: Prisma.TransactionIsolationLevel }): $Utils.JsPromise<R>


  $extends: $Extensions.ExtendsHook<"extends", Prisma.TypeMapCb<ClientOptions>, ExtArgs, $Utils.Call<Prisma.TypeMapCb<ClientOptions>, {
    extArgs: ExtArgs
  }>>

      /**
   * `prisma.account`: Exposes CRUD operations for the **Account** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Accounts
    * const accounts = await prisma.account.findMany()
    * ```
    */
  get account(): Prisma.AccountDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.session`: Exposes CRUD operations for the **Session** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Sessions
    * const sessions = await prisma.session.findMany()
    * ```
    */
  get session(): Prisma.SessionDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.user`: Exposes CRUD operations for the **User** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more Users
    * const users = await prisma.user.findMany()
    * ```
    */
  get user(): Prisma.UserDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.verificationToken`: Exposes CRUD operations for the **VerificationToken** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more VerificationTokens
    * const verificationTokens = await prisma.verificationToken.findMany()
    * ```
    */
  get verificationToken(): Prisma.VerificationTokenDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.emailVerificationRequest`: Exposes CRUD operations for the **EmailVerificationRequest** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more EmailVerificationRequests
    * const emailVerificationRequests = await prisma.emailVerificationRequest.findMany()
    * ```
    */
  get emailVerificationRequest(): Prisma.EmailVerificationRequestDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.localUserProfile`: Exposes CRUD operations for the **LocalUserProfile** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more LocalUserProfiles
    * const localUserProfiles = await prisma.localUserProfile.findMany()
    * ```
    */
  get localUserProfile(): Prisma.LocalUserProfileDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.localArticle`: Exposes CRUD operations for the **LocalArticle** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more LocalArticles
    * const localArticles = await prisma.localArticle.findMany()
    * ```
    */
  get localArticle(): Prisma.LocalArticleDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.feedSync`: Exposes CRUD operations for the **FeedSync** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more FeedSyncs
    * const feedSyncs = await prisma.feedSync.findMany()
    * ```
    */
  get feedSync(): Prisma.FeedSyncDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.feedItem`: Exposes CRUD operations for the **FeedItem** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more FeedItems
    * const feedItems = await prisma.feedItem.findMany()
    * ```
    */
  get feedItem(): Prisma.FeedItemDelegate<ExtArgs, ClientOptions>;

  /**
   * `prisma.syncJob`: Exposes CRUD operations for the **SyncJob** model.
    * Example usage:
    * ```ts
    * // Fetch zero or more SyncJobs
    * const syncJobs = await prisma.syncJob.findMany()
    * ```
    */
  get syncJob(): Prisma.SyncJobDelegate<ExtArgs, ClientOptions>;
}

export namespace Prisma {
  export import DMMF = runtime.DMMF

  export type PrismaPromise<T> = $Public.PrismaPromise<T>

  /**
   * Validator
   */
  export import validator = runtime.Public.validator

  /**
   * Prisma Errors
   */
  export import PrismaClientKnownRequestError = runtime.PrismaClientKnownRequestError
  export import PrismaClientUnknownRequestError = runtime.PrismaClientUnknownRequestError
  export import PrismaClientRustPanicError = runtime.PrismaClientRustPanicError
  export import PrismaClientInitializationError = runtime.PrismaClientInitializationError
  export import PrismaClientValidationError = runtime.PrismaClientValidationError

  /**
   * Re-export of sql-template-tag
   */
  export import sql = runtime.sqltag
  export import empty = runtime.empty
  export import join = runtime.join
  export import raw = runtime.raw
  export import Sql = runtime.Sql



  /**
   * Decimal.js
   */
  export import Decimal = runtime.Decimal

  export type DecimalJsLike = runtime.DecimalJsLike

  /**
   * Metrics
   */
  export type Metrics = runtime.Metrics
  export type Metric<T> = runtime.Metric<T>
  export type MetricHistogram = runtime.MetricHistogram
  export type MetricHistogramBucket = runtime.MetricHistogramBucket

  /**
  * Extensions
  */
  export import Extension = $Extensions.UserArgs
  export import getExtensionContext = runtime.Extensions.getExtensionContext
  export import Args = $Public.Args
  export import Payload = $Public.Payload
  export import Result = $Public.Result
  export import Exact = $Public.Exact

  /**
   * Prisma Client JS version: 6.12.0
   * Query Engine version: 8047c96bbd92db98a2abc7c9323ce77c02c89dbc
   */
  export type PrismaVersion = {
    client: string
  }

  export const prismaVersion: PrismaVersion

  /**
   * Utility Types
   */


  export import JsonObject = runtime.JsonObject
  export import JsonArray = runtime.JsonArray
  export import JsonValue = runtime.JsonValue
  export import InputJsonObject = runtime.InputJsonObject
  export import InputJsonArray = runtime.InputJsonArray
  export import InputJsonValue = runtime.InputJsonValue

  /**
   * Types of the values used to represent different kinds of `null` values when working with JSON fields.
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  namespace NullTypes {
    /**
    * Type of `Prisma.DbNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.DbNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class DbNull {
      private DbNull: never
      private constructor()
    }

    /**
    * Type of `Prisma.JsonNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.JsonNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class JsonNull {
      private JsonNull: never
      private constructor()
    }

    /**
    * Type of `Prisma.AnyNull`.
    *
    * You cannot use other instances of this class. Please use the `Prisma.AnyNull` value.
    *
    * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
    */
    class AnyNull {
      private AnyNull: never
      private constructor()
    }
  }

  /**
   * Helper for filtering JSON entries that have `null` on the database (empty on the db)
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const DbNull: NullTypes.DbNull

  /**
   * Helper for filtering JSON entries that have JSON `null` values (not empty on the db)
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const JsonNull: NullTypes.JsonNull

  /**
   * Helper for filtering JSON entries that are `Prisma.DbNull` or `Prisma.JsonNull`
   *
   * @see https://www.prisma.io/docs/concepts/components/prisma-client/working-with-fields/working-with-json-fields#filtering-on-a-json-field
   */
  export const AnyNull: NullTypes.AnyNull

  type SelectAndInclude = {
    select: any
    include: any
  }

  type SelectAndOmit = {
    select: any
    omit: any
  }

  /**
   * Get the type of the value, that the Promise holds.
   */
  export type PromiseType<T extends PromiseLike<any>> = T extends PromiseLike<infer U> ? U : T;

  /**
   * Get the return type of a function which returns a Promise.
   */
  export type PromiseReturnType<T extends (...args: any) => $Utils.JsPromise<any>> = PromiseType<ReturnType<T>>

  /**
   * From T, pick a set of properties whose keys are in the union K
   */
  type Prisma__Pick<T, K extends keyof T> = {
      [P in K]: T[P];
  };


  export type Enumerable<T> = T | Array<T>;

  export type RequiredKeys<T> = {
    [K in keyof T]-?: {} extends Prisma__Pick<T, K> ? never : K
  }[keyof T]

  export type TruthyKeys<T> = keyof {
    [K in keyof T as T[K] extends false | undefined | null ? never : K]: K
  }

  export type TrueKeys<T> = TruthyKeys<Prisma__Pick<T, RequiredKeys<T>>>

  /**
   * Subset
   * @desc From `T` pick properties that exist in `U`. Simple version of Intersection
   */
  export type Subset<T, U> = {
    [key in keyof T]: key extends keyof U ? T[key] : never;
  };

  /**
   * SelectSubset
   * @desc From `T` pick properties that exist in `U`. Simple version of Intersection.
   * Additionally, it validates, if both select and include are present. If the case, it errors.
   */
  export type SelectSubset<T, U> = {
    [key in keyof T]: key extends keyof U ? T[key] : never
  } &
    (T extends SelectAndInclude
      ? 'Please either choose `select` or `include`.'
      : T extends SelectAndOmit
        ? 'Please either choose `select` or `omit`.'
        : {})

  /**
   * Subset + Intersection
   * @desc From `T` pick properties that exist in `U` and intersect `K`
   */
  export type SubsetIntersection<T, U, K> = {
    [key in keyof T]: key extends keyof U ? T[key] : never
  } &
    K

  type Without<T, U> = { [P in Exclude<keyof T, keyof U>]?: never };

  /**
   * XOR is needed to have a real mutually exclusive union type
   * https://stackoverflow.com/questions/42123407/does-typescript-support-mutually-exclusive-types
   */
  type XOR<T, U> =
    T extends object ?
    U extends object ?
      (Without<T, U> & U) | (Without<U, T> & T)
    : U : T


  /**
   * Is T a Record?
   */
  type IsObject<T extends any> = T extends Array<any>
  ? False
  : T extends Date
  ? False
  : T extends Uint8Array
  ? False
  : T extends BigInt
  ? False
  : T extends object
  ? True
  : False


  /**
   * If it's T[], return T
   */
  export type UnEnumerate<T extends unknown> = T extends Array<infer U> ? U : T

  /**
   * From ts-toolbelt
   */

  type __Either<O extends object, K extends Key> = Omit<O, K> &
    {
      // Merge all but K
      [P in K]: Prisma__Pick<O, P & keyof O> // With K possibilities
    }[K]

  type EitherStrict<O extends object, K extends Key> = Strict<__Either<O, K>>

  type EitherLoose<O extends object, K extends Key> = ComputeRaw<__Either<O, K>>

  type _Either<
    O extends object,
    K extends Key,
    strict extends Boolean
  > = {
    1: EitherStrict<O, K>
    0: EitherLoose<O, K>
  }[strict]

  type Either<
    O extends object,
    K extends Key,
    strict extends Boolean = 1
  > = O extends unknown ? _Either<O, K, strict> : never

  export type Union = any

  type PatchUndefined<O extends object, O1 extends object> = {
    [K in keyof O]: O[K] extends undefined ? At<O1, K> : O[K]
  } & {}

  /** Helper Types for "Merge" **/
  export type IntersectOf<U extends Union> = (
    U extends unknown ? (k: U) => void : never
  ) extends (k: infer I) => void
    ? I
    : never

  export type Overwrite<O extends object, O1 extends object> = {
      [K in keyof O]: K extends keyof O1 ? O1[K] : O[K];
  } & {};

  type _Merge<U extends object> = IntersectOf<Overwrite<U, {
      [K in keyof U]-?: At<U, K>;
  }>>;

  type Key = string | number | symbol;
  type AtBasic<O extends object, K extends Key> = K extends keyof O ? O[K] : never;
  type AtStrict<O extends object, K extends Key> = O[K & keyof O];
  type AtLoose<O extends object, K extends Key> = O extends unknown ? AtStrict<O, K> : never;
  export type At<O extends object, K extends Key, strict extends Boolean = 1> = {
      1: AtStrict<O, K>;
      0: AtLoose<O, K>;
  }[strict];

  export type ComputeRaw<A extends any> = A extends Function ? A : {
    [K in keyof A]: A[K];
  } & {};

  export type OptionalFlat<O> = {
    [K in keyof O]?: O[K];
  } & {};

  type _Record<K extends keyof any, T> = {
    [P in K]: T;
  };

  // cause typescript not to expand types and preserve names
  type NoExpand<T> = T extends unknown ? T : never;

  // this type assumes the passed object is entirely optional
  type AtLeast<O extends object, K extends string> = NoExpand<
    O extends unknown
    ? | (K extends keyof O ? { [P in K]: O[P] } & O : O)
      | {[P in keyof O as P extends K ? P : never]-?: O[P]} & O
    : never>;

  type _Strict<U, _U = U> = U extends unknown ? U & OptionalFlat<_Record<Exclude<Keys<_U>, keyof U>, never>> : never;

  export type Strict<U extends object> = ComputeRaw<_Strict<U>>;
  /** End Helper Types for "Merge" **/

  export type Merge<U extends object> = ComputeRaw<_Merge<Strict<U>>>;

  /**
  A [[Boolean]]
  */
  export type Boolean = True | False

  // /**
  // 1
  // */
  export type True = 1

  /**
  0
  */
  export type False = 0

  export type Not<B extends Boolean> = {
    0: 1
    1: 0
  }[B]

  export type Extends<A1 extends any, A2 extends any> = [A1] extends [never]
    ? 0 // anything `never` is false
    : A1 extends A2
    ? 1
    : 0

  export type Has<U extends Union, U1 extends Union> = Not<
    Extends<Exclude<U1, U>, U1>
  >

  export type Or<B1 extends Boolean, B2 extends Boolean> = {
    0: {
      0: 0
      1: 1
    }
    1: {
      0: 1
      1: 1
    }
  }[B1][B2]

  export type Keys<U extends Union> = U extends unknown ? keyof U : never

  type Cast<A, B> = A extends B ? A : B;

  export const type: unique symbol;



  /**
   * Used by group by
   */

  export type GetScalarType<T, O> = O extends object ? {
    [P in keyof T]: P extends keyof O
      ? O[P]
      : never
  } : never

  type FieldPaths<
    T,
    U = Omit<T, '_avg' | '_sum' | '_count' | '_min' | '_max'>
  > = IsObject<T> extends True ? U : T

  type GetHavingFields<T> = {
    [K in keyof T]: Or<
      Or<Extends<'OR', K>, Extends<'AND', K>>,
      Extends<'NOT', K>
    > extends True
      ? // infer is only needed to not hit TS limit
        // based on the brilliant idea of Pierre-Antoine Mills
        // https://github.com/microsoft/TypeScript/issues/30188#issuecomment-478938437
        T[K] extends infer TK
        ? GetHavingFields<UnEnumerate<TK> extends object ? Merge<UnEnumerate<TK>> : never>
        : never
      : {} extends FieldPaths<T[K]>
      ? never
      : K
  }[keyof T]

  /**
   * Convert tuple to union
   */
  type _TupleToUnion<T> = T extends (infer E)[] ? E : never
  type TupleToUnion<K extends readonly any[]> = _TupleToUnion<K>
  type MaybeTupleToUnion<T> = T extends any[] ? TupleToUnion<T> : T

  /**
   * Like `Pick`, but additionally can also accept an array of keys
   */
  type PickEnumerable<T, K extends Enumerable<keyof T> | keyof T> = Prisma__Pick<T, MaybeTupleToUnion<K>>

  /**
   * Exclude all keys with underscores
   */
  type ExcludeUnderscoreKeys<T extends string> = T extends `_${string}` ? never : T


  export type FieldRef<Model, FieldType> = runtime.FieldRef<Model, FieldType>

  type FieldRefInputType<Model, FieldType> = Model extends never ? never : FieldRef<Model, FieldType>


  export const ModelName: {
    Account: 'Account',
    Session: 'Session',
    User: 'User',
    VerificationToken: 'VerificationToken',
    EmailVerificationRequest: 'EmailVerificationRequest',
    LocalUserProfile: 'LocalUserProfile',
    LocalArticle: 'LocalArticle',
    FeedSync: 'FeedSync',
    FeedItem: 'FeedItem',
    SyncJob: 'SyncJob'
  };

  export type ModelName = (typeof ModelName)[keyof typeof ModelName]


  export type Datasources = {
    db?: Datasource
  }

  interface TypeMapCb<ClientOptions = {}> extends $Utils.Fn<{extArgs: $Extensions.InternalArgs }, $Utils.Record<string, any>> {
    returns: Prisma.TypeMap<this['params']['extArgs'], ClientOptions extends { omit: infer OmitOptions } ? OmitOptions : {}>
  }

  export type TypeMap<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> = {
    globalOmitOptions: {
      omit: GlobalOmitOptions
    }
    meta: {
      modelProps: "account" | "session" | "user" | "verificationToken" | "emailVerificationRequest" | "localUserProfile" | "localArticle" | "feedSync" | "feedItem" | "syncJob"
      txIsolationLevel: Prisma.TransactionIsolationLevel
    }
    model: {
      Account: {
        payload: Prisma.$AccountPayload<ExtArgs>
        fields: Prisma.AccountFieldRefs
        operations: {
          findUnique: {
            args: Prisma.AccountFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.AccountFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>
          }
          findFirst: {
            args: Prisma.AccountFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.AccountFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>
          }
          findMany: {
            args: Prisma.AccountFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>[]
          }
          create: {
            args: Prisma.AccountCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>
          }
          createMany: {
            args: Prisma.AccountCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.AccountCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>[]
          }
          delete: {
            args: Prisma.AccountDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>
          }
          update: {
            args: Prisma.AccountUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>
          }
          deleteMany: {
            args: Prisma.AccountDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.AccountUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.AccountUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>[]
          }
          upsert: {
            args: Prisma.AccountUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$AccountPayload>
          }
          aggregate: {
            args: Prisma.AccountAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateAccount>
          }
          groupBy: {
            args: Prisma.AccountGroupByArgs<ExtArgs>
            result: $Utils.Optional<AccountGroupByOutputType>[]
          }
          count: {
            args: Prisma.AccountCountArgs<ExtArgs>
            result: $Utils.Optional<AccountCountAggregateOutputType> | number
          }
        }
      }
      Session: {
        payload: Prisma.$SessionPayload<ExtArgs>
        fields: Prisma.SessionFieldRefs
        operations: {
          findUnique: {
            args: Prisma.SessionFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.SessionFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>
          }
          findFirst: {
            args: Prisma.SessionFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.SessionFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>
          }
          findMany: {
            args: Prisma.SessionFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>[]
          }
          create: {
            args: Prisma.SessionCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>
          }
          createMany: {
            args: Prisma.SessionCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.SessionCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>[]
          }
          delete: {
            args: Prisma.SessionDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>
          }
          update: {
            args: Prisma.SessionUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>
          }
          deleteMany: {
            args: Prisma.SessionDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.SessionUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.SessionUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>[]
          }
          upsert: {
            args: Prisma.SessionUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SessionPayload>
          }
          aggregate: {
            args: Prisma.SessionAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateSession>
          }
          groupBy: {
            args: Prisma.SessionGroupByArgs<ExtArgs>
            result: $Utils.Optional<SessionGroupByOutputType>[]
          }
          count: {
            args: Prisma.SessionCountArgs<ExtArgs>
            result: $Utils.Optional<SessionCountAggregateOutputType> | number
          }
        }
      }
      User: {
        payload: Prisma.$UserPayload<ExtArgs>
        fields: Prisma.UserFieldRefs
        operations: {
          findUnique: {
            args: Prisma.UserFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.UserFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          findFirst: {
            args: Prisma.UserFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.UserFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          findMany: {
            args: Prisma.UserFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          create: {
            args: Prisma.UserCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          createMany: {
            args: Prisma.UserCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.UserCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          delete: {
            args: Prisma.UserDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          update: {
            args: Prisma.UserUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          deleteMany: {
            args: Prisma.UserDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.UserUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.UserUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>[]
          }
          upsert: {
            args: Prisma.UserUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$UserPayload>
          }
          aggregate: {
            args: Prisma.UserAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateUser>
          }
          groupBy: {
            args: Prisma.UserGroupByArgs<ExtArgs>
            result: $Utils.Optional<UserGroupByOutputType>[]
          }
          count: {
            args: Prisma.UserCountArgs<ExtArgs>
            result: $Utils.Optional<UserCountAggregateOutputType> | number
          }
        }
      }
      VerificationToken: {
        payload: Prisma.$VerificationTokenPayload<ExtArgs>
        fields: Prisma.VerificationTokenFieldRefs
        operations: {
          findUnique: {
            args: Prisma.VerificationTokenFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.VerificationTokenFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>
          }
          findFirst: {
            args: Prisma.VerificationTokenFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.VerificationTokenFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>
          }
          findMany: {
            args: Prisma.VerificationTokenFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>[]
          }
          create: {
            args: Prisma.VerificationTokenCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>
          }
          createMany: {
            args: Prisma.VerificationTokenCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.VerificationTokenCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>[]
          }
          delete: {
            args: Prisma.VerificationTokenDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>
          }
          update: {
            args: Prisma.VerificationTokenUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>
          }
          deleteMany: {
            args: Prisma.VerificationTokenDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.VerificationTokenUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.VerificationTokenUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>[]
          }
          upsert: {
            args: Prisma.VerificationTokenUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$VerificationTokenPayload>
          }
          aggregate: {
            args: Prisma.VerificationTokenAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateVerificationToken>
          }
          groupBy: {
            args: Prisma.VerificationTokenGroupByArgs<ExtArgs>
            result: $Utils.Optional<VerificationTokenGroupByOutputType>[]
          }
          count: {
            args: Prisma.VerificationTokenCountArgs<ExtArgs>
            result: $Utils.Optional<VerificationTokenCountAggregateOutputType> | number
          }
        }
      }
      EmailVerificationRequest: {
        payload: Prisma.$EmailVerificationRequestPayload<ExtArgs>
        fields: Prisma.EmailVerificationRequestFieldRefs
        operations: {
          findUnique: {
            args: Prisma.EmailVerificationRequestFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.EmailVerificationRequestFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>
          }
          findFirst: {
            args: Prisma.EmailVerificationRequestFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.EmailVerificationRequestFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>
          }
          findMany: {
            args: Prisma.EmailVerificationRequestFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>[]
          }
          create: {
            args: Prisma.EmailVerificationRequestCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>
          }
          createMany: {
            args: Prisma.EmailVerificationRequestCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.EmailVerificationRequestCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>[]
          }
          delete: {
            args: Prisma.EmailVerificationRequestDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>
          }
          update: {
            args: Prisma.EmailVerificationRequestUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>
          }
          deleteMany: {
            args: Prisma.EmailVerificationRequestDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.EmailVerificationRequestUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.EmailVerificationRequestUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>[]
          }
          upsert: {
            args: Prisma.EmailVerificationRequestUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$EmailVerificationRequestPayload>
          }
          aggregate: {
            args: Prisma.EmailVerificationRequestAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateEmailVerificationRequest>
          }
          groupBy: {
            args: Prisma.EmailVerificationRequestGroupByArgs<ExtArgs>
            result: $Utils.Optional<EmailVerificationRequestGroupByOutputType>[]
          }
          count: {
            args: Prisma.EmailVerificationRequestCountArgs<ExtArgs>
            result: $Utils.Optional<EmailVerificationRequestCountAggregateOutputType> | number
          }
        }
      }
      LocalUserProfile: {
        payload: Prisma.$LocalUserProfilePayload<ExtArgs>
        fields: Prisma.LocalUserProfileFieldRefs
        operations: {
          findUnique: {
            args: Prisma.LocalUserProfileFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.LocalUserProfileFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>
          }
          findFirst: {
            args: Prisma.LocalUserProfileFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.LocalUserProfileFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>
          }
          findMany: {
            args: Prisma.LocalUserProfileFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>[]
          }
          create: {
            args: Prisma.LocalUserProfileCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>
          }
          createMany: {
            args: Prisma.LocalUserProfileCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.LocalUserProfileCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>[]
          }
          delete: {
            args: Prisma.LocalUserProfileDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>
          }
          update: {
            args: Prisma.LocalUserProfileUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>
          }
          deleteMany: {
            args: Prisma.LocalUserProfileDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.LocalUserProfileUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.LocalUserProfileUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>[]
          }
          upsert: {
            args: Prisma.LocalUserProfileUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalUserProfilePayload>
          }
          aggregate: {
            args: Prisma.LocalUserProfileAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateLocalUserProfile>
          }
          groupBy: {
            args: Prisma.LocalUserProfileGroupByArgs<ExtArgs>
            result: $Utils.Optional<LocalUserProfileGroupByOutputType>[]
          }
          count: {
            args: Prisma.LocalUserProfileCountArgs<ExtArgs>
            result: $Utils.Optional<LocalUserProfileCountAggregateOutputType> | number
          }
        }
      }
      LocalArticle: {
        payload: Prisma.$LocalArticlePayload<ExtArgs>
        fields: Prisma.LocalArticleFieldRefs
        operations: {
          findUnique: {
            args: Prisma.LocalArticleFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.LocalArticleFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>
          }
          findFirst: {
            args: Prisma.LocalArticleFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.LocalArticleFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>
          }
          findMany: {
            args: Prisma.LocalArticleFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>[]
          }
          create: {
            args: Prisma.LocalArticleCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>
          }
          createMany: {
            args: Prisma.LocalArticleCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.LocalArticleCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>[]
          }
          delete: {
            args: Prisma.LocalArticleDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>
          }
          update: {
            args: Prisma.LocalArticleUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>
          }
          deleteMany: {
            args: Prisma.LocalArticleDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.LocalArticleUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.LocalArticleUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>[]
          }
          upsert: {
            args: Prisma.LocalArticleUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$LocalArticlePayload>
          }
          aggregate: {
            args: Prisma.LocalArticleAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateLocalArticle>
          }
          groupBy: {
            args: Prisma.LocalArticleGroupByArgs<ExtArgs>
            result: $Utils.Optional<LocalArticleGroupByOutputType>[]
          }
          count: {
            args: Prisma.LocalArticleCountArgs<ExtArgs>
            result: $Utils.Optional<LocalArticleCountAggregateOutputType> | number
          }
        }
      }
      FeedSync: {
        payload: Prisma.$FeedSyncPayload<ExtArgs>
        fields: Prisma.FeedSyncFieldRefs
        operations: {
          findUnique: {
            args: Prisma.FeedSyncFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.FeedSyncFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>
          }
          findFirst: {
            args: Prisma.FeedSyncFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.FeedSyncFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>
          }
          findMany: {
            args: Prisma.FeedSyncFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>[]
          }
          create: {
            args: Prisma.FeedSyncCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>
          }
          createMany: {
            args: Prisma.FeedSyncCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.FeedSyncCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>[]
          }
          delete: {
            args: Prisma.FeedSyncDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>
          }
          update: {
            args: Prisma.FeedSyncUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>
          }
          deleteMany: {
            args: Prisma.FeedSyncDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.FeedSyncUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.FeedSyncUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>[]
          }
          upsert: {
            args: Prisma.FeedSyncUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedSyncPayload>
          }
          aggregate: {
            args: Prisma.FeedSyncAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateFeedSync>
          }
          groupBy: {
            args: Prisma.FeedSyncGroupByArgs<ExtArgs>
            result: $Utils.Optional<FeedSyncGroupByOutputType>[]
          }
          count: {
            args: Prisma.FeedSyncCountArgs<ExtArgs>
            result: $Utils.Optional<FeedSyncCountAggregateOutputType> | number
          }
        }
      }
      FeedItem: {
        payload: Prisma.$FeedItemPayload<ExtArgs>
        fields: Prisma.FeedItemFieldRefs
        operations: {
          findUnique: {
            args: Prisma.FeedItemFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.FeedItemFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>
          }
          findFirst: {
            args: Prisma.FeedItemFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.FeedItemFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>
          }
          findMany: {
            args: Prisma.FeedItemFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>[]
          }
          create: {
            args: Prisma.FeedItemCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>
          }
          createMany: {
            args: Prisma.FeedItemCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.FeedItemCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>[]
          }
          delete: {
            args: Prisma.FeedItemDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>
          }
          update: {
            args: Prisma.FeedItemUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>
          }
          deleteMany: {
            args: Prisma.FeedItemDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.FeedItemUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.FeedItemUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>[]
          }
          upsert: {
            args: Prisma.FeedItemUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$FeedItemPayload>
          }
          aggregate: {
            args: Prisma.FeedItemAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateFeedItem>
          }
          groupBy: {
            args: Prisma.FeedItemGroupByArgs<ExtArgs>
            result: $Utils.Optional<FeedItemGroupByOutputType>[]
          }
          count: {
            args: Prisma.FeedItemCountArgs<ExtArgs>
            result: $Utils.Optional<FeedItemCountAggregateOutputType> | number
          }
        }
      }
      SyncJob: {
        payload: Prisma.$SyncJobPayload<ExtArgs>
        fields: Prisma.SyncJobFieldRefs
        operations: {
          findUnique: {
            args: Prisma.SyncJobFindUniqueArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload> | null
          }
          findUniqueOrThrow: {
            args: Prisma.SyncJobFindUniqueOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>
          }
          findFirst: {
            args: Prisma.SyncJobFindFirstArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload> | null
          }
          findFirstOrThrow: {
            args: Prisma.SyncJobFindFirstOrThrowArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>
          }
          findMany: {
            args: Prisma.SyncJobFindManyArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>[]
          }
          create: {
            args: Prisma.SyncJobCreateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>
          }
          createMany: {
            args: Prisma.SyncJobCreateManyArgs<ExtArgs>
            result: BatchPayload
          }
          createManyAndReturn: {
            args: Prisma.SyncJobCreateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>[]
          }
          delete: {
            args: Prisma.SyncJobDeleteArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>
          }
          update: {
            args: Prisma.SyncJobUpdateArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>
          }
          deleteMany: {
            args: Prisma.SyncJobDeleteManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateMany: {
            args: Prisma.SyncJobUpdateManyArgs<ExtArgs>
            result: BatchPayload
          }
          updateManyAndReturn: {
            args: Prisma.SyncJobUpdateManyAndReturnArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>[]
          }
          upsert: {
            args: Prisma.SyncJobUpsertArgs<ExtArgs>
            result: $Utils.PayloadToResult<Prisma.$SyncJobPayload>
          }
          aggregate: {
            args: Prisma.SyncJobAggregateArgs<ExtArgs>
            result: $Utils.Optional<AggregateSyncJob>
          }
          groupBy: {
            args: Prisma.SyncJobGroupByArgs<ExtArgs>
            result: $Utils.Optional<SyncJobGroupByOutputType>[]
          }
          count: {
            args: Prisma.SyncJobCountArgs<ExtArgs>
            result: $Utils.Optional<SyncJobCountAggregateOutputType> | number
          }
        }
      }
    }
  } & {
    other: {
      payload: any
      operations: {
        $executeRaw: {
          args: [query: TemplateStringsArray | Prisma.Sql, ...values: any[]],
          result: any
        }
        $executeRawUnsafe: {
          args: [query: string, ...values: any[]],
          result: any
        }
        $queryRaw: {
          args: [query: TemplateStringsArray | Prisma.Sql, ...values: any[]],
          result: any
        }
        $queryRawUnsafe: {
          args: [query: string, ...values: any[]],
          result: any
        }
      }
    }
  }
  export const defineExtension: $Extensions.ExtendsHook<"define", Prisma.TypeMapCb, $Extensions.DefaultArgs>
  export type DefaultPrismaClient = PrismaClient
  export type ErrorFormat = 'pretty' | 'colorless' | 'minimal'
  export interface PrismaClientOptions {
    /**
     * Overwrites the datasource url from your schema.prisma file
     */
    datasources?: Datasources
    /**
     * Overwrites the datasource url from your schema.prisma file
     */
    datasourceUrl?: string
    /**
     * @default "colorless"
     */
    errorFormat?: ErrorFormat
    /**
     * @example
     * ```
     * // Defaults to stdout
     * log: ['query', 'info', 'warn', 'error']
     * 
     * // Emit as events
     * log: [
     *   { emit: 'stdout', level: 'query' },
     *   { emit: 'stdout', level: 'info' },
     *   { emit: 'stdout', level: 'warn' }
     *   { emit: 'stdout', level: 'error' }
     * ]
     * ```
     * Read more in our [docs](https://www.prisma.io/docs/reference/tools-and-interfaces/prisma-client/logging#the-log-option).
     */
    log?: (LogLevel | LogDefinition)[]
    /**
     * The default values for transactionOptions
     * maxWait ?= 2000
     * timeout ?= 5000
     */
    transactionOptions?: {
      maxWait?: number
      timeout?: number
      isolationLevel?: Prisma.TransactionIsolationLevel
    }
    /**
     * Global configuration for omitting model fields by default.
     * 
     * @example
     * ```
     * const prisma = new PrismaClient({
     *   omit: {
     *     user: {
     *       password: true
     *     }
     *   }
     * })
     * ```
     */
    omit?: Prisma.GlobalOmitConfig
  }
  export type GlobalOmitConfig = {
    account?: AccountOmit
    session?: SessionOmit
    user?: UserOmit
    verificationToken?: VerificationTokenOmit
    emailVerificationRequest?: EmailVerificationRequestOmit
    localUserProfile?: LocalUserProfileOmit
    localArticle?: LocalArticleOmit
    feedSync?: FeedSyncOmit
    feedItem?: FeedItemOmit
    syncJob?: SyncJobOmit
  }

  /* Types for Logging */
  export type LogLevel = 'info' | 'query' | 'warn' | 'error'
  export type LogDefinition = {
    level: LogLevel
    emit: 'stdout' | 'event'
  }

  export type GetLogType<T extends LogLevel | LogDefinition> = T extends LogDefinition ? T['emit'] extends 'event' ? T['level'] : never : never
  export type GetEvents<T extends any> = T extends Array<LogLevel | LogDefinition> ?
    GetLogType<T[0]> | GetLogType<T[1]> | GetLogType<T[2]> | GetLogType<T[3]>
    : never

  export type QueryEvent = {
    timestamp: Date
    query: string
    params: string
    duration: number
    target: string
  }

  export type LogEvent = {
    timestamp: Date
    message: string
    target: string
  }
  /* End Types for Logging */


  export type PrismaAction =
    | 'findUnique'
    | 'findUniqueOrThrow'
    | 'findMany'
    | 'findFirst'
    | 'findFirstOrThrow'
    | 'create'
    | 'createMany'
    | 'createManyAndReturn'
    | 'update'
    | 'updateMany'
    | 'updateManyAndReturn'
    | 'upsert'
    | 'delete'
    | 'deleteMany'
    | 'executeRaw'
    | 'queryRaw'
    | 'aggregate'
    | 'count'
    | 'runCommandRaw'
    | 'findRaw'
    | 'groupBy'

  /**
   * These options are being passed into the middleware as "params"
   */
  export type MiddlewareParams = {
    model?: ModelName
    action: PrismaAction
    args: any
    dataPath: string[]
    runInTransaction: boolean
  }

  /**
   * The `T` type makes sure, that the `return proceed` is not forgotten in the middleware implementation
   */
  export type Middleware<T = any> = (
    params: MiddlewareParams,
    next: (params: MiddlewareParams) => $Utils.JsPromise<T>,
  ) => $Utils.JsPromise<T>

  // tested in getLogLevel.test.ts
  export function getLogLevel(log: Array<LogLevel | LogDefinition>): LogLevel | undefined;

  /**
   * `PrismaClient` proxy available in interactive transactions.
   */
  export type TransactionClient = Omit<Prisma.DefaultPrismaClient, runtime.ITXClientDenyList>

  export type Datasource = {
    url?: string
  }

  /**
   * Count Types
   */


  /**
   * Count Type UserCountOutputType
   */

  export type UserCountOutputType = {
    accounts: number
    sessions: number
  }

  export type UserCountOutputTypeSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    accounts?: boolean | UserCountOutputTypeCountAccountsArgs
    sessions?: boolean | UserCountOutputTypeCountSessionsArgs
  }

  // Custom InputTypes
  /**
   * UserCountOutputType without action
   */
  export type UserCountOutputTypeDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the UserCountOutputType
     */
    select?: UserCountOutputTypeSelect<ExtArgs> | null
  }

  /**
   * UserCountOutputType without action
   */
  export type UserCountOutputTypeCountAccountsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: AccountWhereInput
  }

  /**
   * UserCountOutputType without action
   */
  export type UserCountOutputTypeCountSessionsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: SessionWhereInput
  }


  /**
   * Count Type LocalUserProfileCountOutputType
   */

  export type LocalUserProfileCountOutputType = {
    feedSyncs: number
  }

  export type LocalUserProfileCountOutputTypeSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedSyncs?: boolean | LocalUserProfileCountOutputTypeCountFeedSyncsArgs
  }

  // Custom InputTypes
  /**
   * LocalUserProfileCountOutputType without action
   */
  export type LocalUserProfileCountOutputTypeDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfileCountOutputType
     */
    select?: LocalUserProfileCountOutputTypeSelect<ExtArgs> | null
  }

  /**
   * LocalUserProfileCountOutputType without action
   */
  export type LocalUserProfileCountOutputTypeCountFeedSyncsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FeedSyncWhereInput
  }


  /**
   * Count Type LocalArticleCountOutputType
   */

  export type LocalArticleCountOutputType = {
    feedItems: number
  }

  export type LocalArticleCountOutputTypeSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedItems?: boolean | LocalArticleCountOutputTypeCountFeedItemsArgs
  }

  // Custom InputTypes
  /**
   * LocalArticleCountOutputType without action
   */
  export type LocalArticleCountOutputTypeDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticleCountOutputType
     */
    select?: LocalArticleCountOutputTypeSelect<ExtArgs> | null
  }

  /**
   * LocalArticleCountOutputType without action
   */
  export type LocalArticleCountOutputTypeCountFeedItemsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FeedItemWhereInput
  }


  /**
   * Count Type FeedSyncCountOutputType
   */

  export type FeedSyncCountOutputType = {
    feedItems: number
  }

  export type FeedSyncCountOutputTypeSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedItems?: boolean | FeedSyncCountOutputTypeCountFeedItemsArgs
  }

  // Custom InputTypes
  /**
   * FeedSyncCountOutputType without action
   */
  export type FeedSyncCountOutputTypeDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSyncCountOutputType
     */
    select?: FeedSyncCountOutputTypeSelect<ExtArgs> | null
  }

  /**
   * FeedSyncCountOutputType without action
   */
  export type FeedSyncCountOutputTypeCountFeedItemsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FeedItemWhereInput
  }


  /**
   * Models
   */

  /**
   * Model Account
   */

  export type AggregateAccount = {
    _count: AccountCountAggregateOutputType | null
    _avg: AccountAvgAggregateOutputType | null
    _sum: AccountSumAggregateOutputType | null
    _min: AccountMinAggregateOutputType | null
    _max: AccountMaxAggregateOutputType | null
  }

  export type AccountAvgAggregateOutputType = {
    expires_at: number | null
  }

  export type AccountSumAggregateOutputType = {
    expires_at: number | null
  }

  export type AccountMinAggregateOutputType = {
    id: string | null
    userId: string | null
    type: string | null
    provider: string | null
    providerAccountId: string | null
    refresh_token: string | null
    access_token: string | null
    expires_at: number | null
    token_type: string | null
    scope: string | null
    id_token: string | null
    session_state: string | null
  }

  export type AccountMaxAggregateOutputType = {
    id: string | null
    userId: string | null
    type: string | null
    provider: string | null
    providerAccountId: string | null
    refresh_token: string | null
    access_token: string | null
    expires_at: number | null
    token_type: string | null
    scope: string | null
    id_token: string | null
    session_state: string | null
  }

  export type AccountCountAggregateOutputType = {
    id: number
    userId: number
    type: number
    provider: number
    providerAccountId: number
    refresh_token: number
    access_token: number
    expires_at: number
    token_type: number
    scope: number
    id_token: number
    session_state: number
    _all: number
  }


  export type AccountAvgAggregateInputType = {
    expires_at?: true
  }

  export type AccountSumAggregateInputType = {
    expires_at?: true
  }

  export type AccountMinAggregateInputType = {
    id?: true
    userId?: true
    type?: true
    provider?: true
    providerAccountId?: true
    refresh_token?: true
    access_token?: true
    expires_at?: true
    token_type?: true
    scope?: true
    id_token?: true
    session_state?: true
  }

  export type AccountMaxAggregateInputType = {
    id?: true
    userId?: true
    type?: true
    provider?: true
    providerAccountId?: true
    refresh_token?: true
    access_token?: true
    expires_at?: true
    token_type?: true
    scope?: true
    id_token?: true
    session_state?: true
  }

  export type AccountCountAggregateInputType = {
    id?: true
    userId?: true
    type?: true
    provider?: true
    providerAccountId?: true
    refresh_token?: true
    access_token?: true
    expires_at?: true
    token_type?: true
    scope?: true
    id_token?: true
    session_state?: true
    _all?: true
  }

  export type AccountAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Account to aggregate.
     */
    where?: AccountWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Accounts to fetch.
     */
    orderBy?: AccountOrderByWithRelationInput | AccountOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: AccountWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Accounts from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Accounts.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Accounts
    **/
    _count?: true | AccountCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: AccountAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: AccountSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: AccountMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: AccountMaxAggregateInputType
  }

  export type GetAccountAggregateType<T extends AccountAggregateArgs> = {
        [P in keyof T & keyof AggregateAccount]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateAccount[P]>
      : GetScalarType<T[P], AggregateAccount[P]>
  }




  export type AccountGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: AccountWhereInput
    orderBy?: AccountOrderByWithAggregationInput | AccountOrderByWithAggregationInput[]
    by: AccountScalarFieldEnum[] | AccountScalarFieldEnum
    having?: AccountScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: AccountCountAggregateInputType | true
    _avg?: AccountAvgAggregateInputType
    _sum?: AccountSumAggregateInputType
    _min?: AccountMinAggregateInputType
    _max?: AccountMaxAggregateInputType
  }

  export type AccountGroupByOutputType = {
    id: string
    userId: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token: string | null
    access_token: string | null
    expires_at: number | null
    token_type: string | null
    scope: string | null
    id_token: string | null
    session_state: string | null
    _count: AccountCountAggregateOutputType | null
    _avg: AccountAvgAggregateOutputType | null
    _sum: AccountSumAggregateOutputType | null
    _min: AccountMinAggregateOutputType | null
    _max: AccountMaxAggregateOutputType | null
  }

  type GetAccountGroupByPayload<T extends AccountGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<AccountGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof AccountGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], AccountGroupByOutputType[P]>
            : GetScalarType<T[P], AccountGroupByOutputType[P]>
        }
      >
    >


  export type AccountSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    type?: boolean
    provider?: boolean
    providerAccountId?: boolean
    refresh_token?: boolean
    access_token?: boolean
    expires_at?: boolean
    token_type?: boolean
    scope?: boolean
    id_token?: boolean
    session_state?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["account"]>

  export type AccountSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    type?: boolean
    provider?: boolean
    providerAccountId?: boolean
    refresh_token?: boolean
    access_token?: boolean
    expires_at?: boolean
    token_type?: boolean
    scope?: boolean
    id_token?: boolean
    session_state?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["account"]>

  export type AccountSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    type?: boolean
    provider?: boolean
    providerAccountId?: boolean
    refresh_token?: boolean
    access_token?: boolean
    expires_at?: boolean
    token_type?: boolean
    scope?: boolean
    id_token?: boolean
    session_state?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["account"]>

  export type AccountSelectScalar = {
    id?: boolean
    userId?: boolean
    type?: boolean
    provider?: boolean
    providerAccountId?: boolean
    refresh_token?: boolean
    access_token?: boolean
    expires_at?: boolean
    token_type?: boolean
    scope?: boolean
    id_token?: boolean
    session_state?: boolean
  }

  export type AccountOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "userId" | "type" | "provider" | "providerAccountId" | "refresh_token" | "access_token" | "expires_at" | "token_type" | "scope" | "id_token" | "session_state", ExtArgs["result"]["account"]>
  export type AccountInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }
  export type AccountIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }
  export type AccountIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }

  export type $AccountPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "Account"
    objects: {
      user: Prisma.$UserPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      userId: string
      type: string
      provider: string
      providerAccountId: string
      refresh_token: string | null
      access_token: string | null
      expires_at: number | null
      token_type: string | null
      scope: string | null
      id_token: string | null
      session_state: string | null
    }, ExtArgs["result"]["account"]>
    composites: {}
  }

  type AccountGetPayload<S extends boolean | null | undefined | AccountDefaultArgs> = $Result.GetResult<Prisma.$AccountPayload, S>

  type AccountCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<AccountFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: AccountCountAggregateInputType | true
    }

  export interface AccountDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['Account'], meta: { name: 'Account' } }
    /**
     * Find zero or one Account that matches the filter.
     * @param {AccountFindUniqueArgs} args - Arguments to find a Account
     * @example
     * // Get one Account
     * const account = await prisma.account.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends AccountFindUniqueArgs>(args: SelectSubset<T, AccountFindUniqueArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one Account that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {AccountFindUniqueOrThrowArgs} args - Arguments to find a Account
     * @example
     * // Get one Account
     * const account = await prisma.account.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends AccountFindUniqueOrThrowArgs>(args: SelectSubset<T, AccountFindUniqueOrThrowArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Account that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountFindFirstArgs} args - Arguments to find a Account
     * @example
     * // Get one Account
     * const account = await prisma.account.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends AccountFindFirstArgs>(args?: SelectSubset<T, AccountFindFirstArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Account that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountFindFirstOrThrowArgs} args - Arguments to find a Account
     * @example
     * // Get one Account
     * const account = await prisma.account.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends AccountFindFirstOrThrowArgs>(args?: SelectSubset<T, AccountFindFirstOrThrowArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Accounts that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Accounts
     * const accounts = await prisma.account.findMany()
     * 
     * // Get first 10 Accounts
     * const accounts = await prisma.account.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const accountWithIdOnly = await prisma.account.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends AccountFindManyArgs>(args?: SelectSubset<T, AccountFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a Account.
     * @param {AccountCreateArgs} args - Arguments to create a Account.
     * @example
     * // Create one Account
     * const Account = await prisma.account.create({
     *   data: {
     *     // ... data to create a Account
     *   }
     * })
     * 
     */
    create<T extends AccountCreateArgs>(args: SelectSubset<T, AccountCreateArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Accounts.
     * @param {AccountCreateManyArgs} args - Arguments to create many Accounts.
     * @example
     * // Create many Accounts
     * const account = await prisma.account.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends AccountCreateManyArgs>(args?: SelectSubset<T, AccountCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Accounts and returns the data saved in the database.
     * @param {AccountCreateManyAndReturnArgs} args - Arguments to create many Accounts.
     * @example
     * // Create many Accounts
     * const account = await prisma.account.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Accounts and only return the `id`
     * const accountWithIdOnly = await prisma.account.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends AccountCreateManyAndReturnArgs>(args?: SelectSubset<T, AccountCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a Account.
     * @param {AccountDeleteArgs} args - Arguments to delete one Account.
     * @example
     * // Delete one Account
     * const Account = await prisma.account.delete({
     *   where: {
     *     // ... filter to delete one Account
     *   }
     * })
     * 
     */
    delete<T extends AccountDeleteArgs>(args: SelectSubset<T, AccountDeleteArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one Account.
     * @param {AccountUpdateArgs} args - Arguments to update one Account.
     * @example
     * // Update one Account
     * const account = await prisma.account.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends AccountUpdateArgs>(args: SelectSubset<T, AccountUpdateArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Accounts.
     * @param {AccountDeleteManyArgs} args - Arguments to filter Accounts to delete.
     * @example
     * // Delete a few Accounts
     * const { count } = await prisma.account.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends AccountDeleteManyArgs>(args?: SelectSubset<T, AccountDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Accounts.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Accounts
     * const account = await prisma.account.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends AccountUpdateManyArgs>(args: SelectSubset<T, AccountUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Accounts and returns the data updated in the database.
     * @param {AccountUpdateManyAndReturnArgs} args - Arguments to update many Accounts.
     * @example
     * // Update many Accounts
     * const account = await prisma.account.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Accounts and only return the `id`
     * const accountWithIdOnly = await prisma.account.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends AccountUpdateManyAndReturnArgs>(args: SelectSubset<T, AccountUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one Account.
     * @param {AccountUpsertArgs} args - Arguments to update or create a Account.
     * @example
     * // Update or create a Account
     * const account = await prisma.account.upsert({
     *   create: {
     *     // ... data to create a Account
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the Account we want to update
     *   }
     * })
     */
    upsert<T extends AccountUpsertArgs>(args: SelectSubset<T, AccountUpsertArgs<ExtArgs>>): Prisma__AccountClient<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Accounts.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountCountArgs} args - Arguments to filter Accounts to count.
     * @example
     * // Count the number of Accounts
     * const count = await prisma.account.count({
     *   where: {
     *     // ... the filter for the Accounts we want to count
     *   }
     * })
    **/
    count<T extends AccountCountArgs>(
      args?: Subset<T, AccountCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], AccountCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a Account.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends AccountAggregateArgs>(args: Subset<T, AccountAggregateArgs>): Prisma.PrismaPromise<GetAccountAggregateType<T>>

    /**
     * Group by Account.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {AccountGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends AccountGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: AccountGroupByArgs['orderBy'] }
        : { orderBy?: AccountGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, AccountGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetAccountGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the Account model
   */
  readonly fields: AccountFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for Account.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__AccountClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    user<T extends UserDefaultArgs<ExtArgs> = {}>(args?: Subset<T, UserDefaultArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the Account model
   */
  interface AccountFieldRefs {
    readonly id: FieldRef<"Account", 'String'>
    readonly userId: FieldRef<"Account", 'String'>
    readonly type: FieldRef<"Account", 'String'>
    readonly provider: FieldRef<"Account", 'String'>
    readonly providerAccountId: FieldRef<"Account", 'String'>
    readonly refresh_token: FieldRef<"Account", 'String'>
    readonly access_token: FieldRef<"Account", 'String'>
    readonly expires_at: FieldRef<"Account", 'Int'>
    readonly token_type: FieldRef<"Account", 'String'>
    readonly scope: FieldRef<"Account", 'String'>
    readonly id_token: FieldRef<"Account", 'String'>
    readonly session_state: FieldRef<"Account", 'String'>
  }
    

  // Custom InputTypes
  /**
   * Account findUnique
   */
  export type AccountFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * Filter, which Account to fetch.
     */
    where: AccountWhereUniqueInput
  }

  /**
   * Account findUniqueOrThrow
   */
  export type AccountFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * Filter, which Account to fetch.
     */
    where: AccountWhereUniqueInput
  }

  /**
   * Account findFirst
   */
  export type AccountFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * Filter, which Account to fetch.
     */
    where?: AccountWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Accounts to fetch.
     */
    orderBy?: AccountOrderByWithRelationInput | AccountOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Accounts.
     */
    cursor?: AccountWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Accounts from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Accounts.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Accounts.
     */
    distinct?: AccountScalarFieldEnum | AccountScalarFieldEnum[]
  }

  /**
   * Account findFirstOrThrow
   */
  export type AccountFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * Filter, which Account to fetch.
     */
    where?: AccountWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Accounts to fetch.
     */
    orderBy?: AccountOrderByWithRelationInput | AccountOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Accounts.
     */
    cursor?: AccountWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Accounts from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Accounts.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Accounts.
     */
    distinct?: AccountScalarFieldEnum | AccountScalarFieldEnum[]
  }

  /**
   * Account findMany
   */
  export type AccountFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * Filter, which Accounts to fetch.
     */
    where?: AccountWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Accounts to fetch.
     */
    orderBy?: AccountOrderByWithRelationInput | AccountOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Accounts.
     */
    cursor?: AccountWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Accounts from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Accounts.
     */
    skip?: number
    distinct?: AccountScalarFieldEnum | AccountScalarFieldEnum[]
  }

  /**
   * Account create
   */
  export type AccountCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * The data needed to create a Account.
     */
    data: XOR<AccountCreateInput, AccountUncheckedCreateInput>
  }

  /**
   * Account createMany
   */
  export type AccountCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Accounts.
     */
    data: AccountCreateManyInput | AccountCreateManyInput[]
  }

  /**
   * Account createManyAndReturn
   */
  export type AccountCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * The data used to create many Accounts.
     */
    data: AccountCreateManyInput | AccountCreateManyInput[]
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * Account update
   */
  export type AccountUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * The data needed to update a Account.
     */
    data: XOR<AccountUpdateInput, AccountUncheckedUpdateInput>
    /**
     * Choose, which Account to update.
     */
    where: AccountWhereUniqueInput
  }

  /**
   * Account updateMany
   */
  export type AccountUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Accounts.
     */
    data: XOR<AccountUpdateManyMutationInput, AccountUncheckedUpdateManyInput>
    /**
     * Filter which Accounts to update
     */
    where?: AccountWhereInput
    /**
     * Limit how many Accounts to update.
     */
    limit?: number
  }

  /**
   * Account updateManyAndReturn
   */
  export type AccountUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * The data used to update Accounts.
     */
    data: XOR<AccountUpdateManyMutationInput, AccountUncheckedUpdateManyInput>
    /**
     * Filter which Accounts to update
     */
    where?: AccountWhereInput
    /**
     * Limit how many Accounts to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * Account upsert
   */
  export type AccountUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * The filter to search for the Account to update in case it exists.
     */
    where: AccountWhereUniqueInput
    /**
     * In case the Account found by the `where` argument doesn't exist, create a new Account with this data.
     */
    create: XOR<AccountCreateInput, AccountUncheckedCreateInput>
    /**
     * In case the Account was found with the provided `where` argument, update it with this data.
     */
    update: XOR<AccountUpdateInput, AccountUncheckedUpdateInput>
  }

  /**
   * Account delete
   */
  export type AccountDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    /**
     * Filter which Account to delete.
     */
    where: AccountWhereUniqueInput
  }

  /**
   * Account deleteMany
   */
  export type AccountDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Accounts to delete
     */
    where?: AccountWhereInput
    /**
     * Limit how many Accounts to delete.
     */
    limit?: number
  }

  /**
   * Account without action
   */
  export type AccountDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
  }


  /**
   * Model Session
   */

  export type AggregateSession = {
    _count: SessionCountAggregateOutputType | null
    _min: SessionMinAggregateOutputType | null
    _max: SessionMaxAggregateOutputType | null
  }

  export type SessionMinAggregateOutputType = {
    id: string | null
    sessionToken: string | null
    userId: string | null
    expires: Date | null
  }

  export type SessionMaxAggregateOutputType = {
    id: string | null
    sessionToken: string | null
    userId: string | null
    expires: Date | null
  }

  export type SessionCountAggregateOutputType = {
    id: number
    sessionToken: number
    userId: number
    expires: number
    _all: number
  }


  export type SessionMinAggregateInputType = {
    id?: true
    sessionToken?: true
    userId?: true
    expires?: true
  }

  export type SessionMaxAggregateInputType = {
    id?: true
    sessionToken?: true
    userId?: true
    expires?: true
  }

  export type SessionCountAggregateInputType = {
    id?: true
    sessionToken?: true
    userId?: true
    expires?: true
    _all?: true
  }

  export type SessionAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Session to aggregate.
     */
    where?: SessionWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Sessions to fetch.
     */
    orderBy?: SessionOrderByWithRelationInput | SessionOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: SessionWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Sessions from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Sessions.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Sessions
    **/
    _count?: true | SessionCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: SessionMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: SessionMaxAggregateInputType
  }

  export type GetSessionAggregateType<T extends SessionAggregateArgs> = {
        [P in keyof T & keyof AggregateSession]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateSession[P]>
      : GetScalarType<T[P], AggregateSession[P]>
  }




  export type SessionGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: SessionWhereInput
    orderBy?: SessionOrderByWithAggregationInput | SessionOrderByWithAggregationInput[]
    by: SessionScalarFieldEnum[] | SessionScalarFieldEnum
    having?: SessionScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: SessionCountAggregateInputType | true
    _min?: SessionMinAggregateInputType
    _max?: SessionMaxAggregateInputType
  }

  export type SessionGroupByOutputType = {
    id: string
    sessionToken: string
    userId: string
    expires: Date
    _count: SessionCountAggregateOutputType | null
    _min: SessionMinAggregateOutputType | null
    _max: SessionMaxAggregateOutputType | null
  }

  type GetSessionGroupByPayload<T extends SessionGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<SessionGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof SessionGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], SessionGroupByOutputType[P]>
            : GetScalarType<T[P], SessionGroupByOutputType[P]>
        }
      >
    >


  export type SessionSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    sessionToken?: boolean
    userId?: boolean
    expires?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["session"]>

  export type SessionSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    sessionToken?: boolean
    userId?: boolean
    expires?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["session"]>

  export type SessionSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    sessionToken?: boolean
    userId?: boolean
    expires?: boolean
    user?: boolean | UserDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["session"]>

  export type SessionSelectScalar = {
    id?: boolean
    sessionToken?: boolean
    userId?: boolean
    expires?: boolean
  }

  export type SessionOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "sessionToken" | "userId" | "expires", ExtArgs["result"]["session"]>
  export type SessionInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }
  export type SessionIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }
  export type SessionIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    user?: boolean | UserDefaultArgs<ExtArgs>
  }

  export type $SessionPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "Session"
    objects: {
      user: Prisma.$UserPayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      sessionToken: string
      userId: string
      expires: Date
    }, ExtArgs["result"]["session"]>
    composites: {}
  }

  type SessionGetPayload<S extends boolean | null | undefined | SessionDefaultArgs> = $Result.GetResult<Prisma.$SessionPayload, S>

  type SessionCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<SessionFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: SessionCountAggregateInputType | true
    }

  export interface SessionDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['Session'], meta: { name: 'Session' } }
    /**
     * Find zero or one Session that matches the filter.
     * @param {SessionFindUniqueArgs} args - Arguments to find a Session
     * @example
     * // Get one Session
     * const session = await prisma.session.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends SessionFindUniqueArgs>(args: SelectSubset<T, SessionFindUniqueArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one Session that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {SessionFindUniqueOrThrowArgs} args - Arguments to find a Session
     * @example
     * // Get one Session
     * const session = await prisma.session.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends SessionFindUniqueOrThrowArgs>(args: SelectSubset<T, SessionFindUniqueOrThrowArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Session that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionFindFirstArgs} args - Arguments to find a Session
     * @example
     * // Get one Session
     * const session = await prisma.session.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends SessionFindFirstArgs>(args?: SelectSubset<T, SessionFindFirstArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first Session that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionFindFirstOrThrowArgs} args - Arguments to find a Session
     * @example
     * // Get one Session
     * const session = await prisma.session.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends SessionFindFirstOrThrowArgs>(args?: SelectSubset<T, SessionFindFirstOrThrowArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Sessions that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Sessions
     * const sessions = await prisma.session.findMany()
     * 
     * // Get first 10 Sessions
     * const sessions = await prisma.session.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const sessionWithIdOnly = await prisma.session.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends SessionFindManyArgs>(args?: SelectSubset<T, SessionFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a Session.
     * @param {SessionCreateArgs} args - Arguments to create a Session.
     * @example
     * // Create one Session
     * const Session = await prisma.session.create({
     *   data: {
     *     // ... data to create a Session
     *   }
     * })
     * 
     */
    create<T extends SessionCreateArgs>(args: SelectSubset<T, SessionCreateArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Sessions.
     * @param {SessionCreateManyArgs} args - Arguments to create many Sessions.
     * @example
     * // Create many Sessions
     * const session = await prisma.session.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends SessionCreateManyArgs>(args?: SelectSubset<T, SessionCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Sessions and returns the data saved in the database.
     * @param {SessionCreateManyAndReturnArgs} args - Arguments to create many Sessions.
     * @example
     * // Create many Sessions
     * const session = await prisma.session.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Sessions and only return the `id`
     * const sessionWithIdOnly = await prisma.session.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends SessionCreateManyAndReturnArgs>(args?: SelectSubset<T, SessionCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a Session.
     * @param {SessionDeleteArgs} args - Arguments to delete one Session.
     * @example
     * // Delete one Session
     * const Session = await prisma.session.delete({
     *   where: {
     *     // ... filter to delete one Session
     *   }
     * })
     * 
     */
    delete<T extends SessionDeleteArgs>(args: SelectSubset<T, SessionDeleteArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one Session.
     * @param {SessionUpdateArgs} args - Arguments to update one Session.
     * @example
     * // Update one Session
     * const session = await prisma.session.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends SessionUpdateArgs>(args: SelectSubset<T, SessionUpdateArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Sessions.
     * @param {SessionDeleteManyArgs} args - Arguments to filter Sessions to delete.
     * @example
     * // Delete a few Sessions
     * const { count } = await prisma.session.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends SessionDeleteManyArgs>(args?: SelectSubset<T, SessionDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Sessions.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Sessions
     * const session = await prisma.session.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends SessionUpdateManyArgs>(args: SelectSubset<T, SessionUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Sessions and returns the data updated in the database.
     * @param {SessionUpdateManyAndReturnArgs} args - Arguments to update many Sessions.
     * @example
     * // Update many Sessions
     * const session = await prisma.session.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Sessions and only return the `id`
     * const sessionWithIdOnly = await prisma.session.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends SessionUpdateManyAndReturnArgs>(args: SelectSubset<T, SessionUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one Session.
     * @param {SessionUpsertArgs} args - Arguments to update or create a Session.
     * @example
     * // Update or create a Session
     * const session = await prisma.session.upsert({
     *   create: {
     *     // ... data to create a Session
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the Session we want to update
     *   }
     * })
     */
    upsert<T extends SessionUpsertArgs>(args: SelectSubset<T, SessionUpsertArgs<ExtArgs>>): Prisma__SessionClient<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Sessions.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionCountArgs} args - Arguments to filter Sessions to count.
     * @example
     * // Count the number of Sessions
     * const count = await prisma.session.count({
     *   where: {
     *     // ... the filter for the Sessions we want to count
     *   }
     * })
    **/
    count<T extends SessionCountArgs>(
      args?: Subset<T, SessionCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], SessionCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a Session.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends SessionAggregateArgs>(args: Subset<T, SessionAggregateArgs>): Prisma.PrismaPromise<GetSessionAggregateType<T>>

    /**
     * Group by Session.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SessionGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends SessionGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: SessionGroupByArgs['orderBy'] }
        : { orderBy?: SessionGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, SessionGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetSessionGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the Session model
   */
  readonly fields: SessionFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for Session.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__SessionClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    user<T extends UserDefaultArgs<ExtArgs> = {}>(args?: Subset<T, UserDefaultArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the Session model
   */
  interface SessionFieldRefs {
    readonly id: FieldRef<"Session", 'String'>
    readonly sessionToken: FieldRef<"Session", 'String'>
    readonly userId: FieldRef<"Session", 'String'>
    readonly expires: FieldRef<"Session", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * Session findUnique
   */
  export type SessionFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * Filter, which Session to fetch.
     */
    where: SessionWhereUniqueInput
  }

  /**
   * Session findUniqueOrThrow
   */
  export type SessionFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * Filter, which Session to fetch.
     */
    where: SessionWhereUniqueInput
  }

  /**
   * Session findFirst
   */
  export type SessionFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * Filter, which Session to fetch.
     */
    where?: SessionWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Sessions to fetch.
     */
    orderBy?: SessionOrderByWithRelationInput | SessionOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Sessions.
     */
    cursor?: SessionWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Sessions from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Sessions.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Sessions.
     */
    distinct?: SessionScalarFieldEnum | SessionScalarFieldEnum[]
  }

  /**
   * Session findFirstOrThrow
   */
  export type SessionFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * Filter, which Session to fetch.
     */
    where?: SessionWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Sessions to fetch.
     */
    orderBy?: SessionOrderByWithRelationInput | SessionOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Sessions.
     */
    cursor?: SessionWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Sessions from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Sessions.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Sessions.
     */
    distinct?: SessionScalarFieldEnum | SessionScalarFieldEnum[]
  }

  /**
   * Session findMany
   */
  export type SessionFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * Filter, which Sessions to fetch.
     */
    where?: SessionWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Sessions to fetch.
     */
    orderBy?: SessionOrderByWithRelationInput | SessionOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Sessions.
     */
    cursor?: SessionWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Sessions from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Sessions.
     */
    skip?: number
    distinct?: SessionScalarFieldEnum | SessionScalarFieldEnum[]
  }

  /**
   * Session create
   */
  export type SessionCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * The data needed to create a Session.
     */
    data: XOR<SessionCreateInput, SessionUncheckedCreateInput>
  }

  /**
   * Session createMany
   */
  export type SessionCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Sessions.
     */
    data: SessionCreateManyInput | SessionCreateManyInput[]
  }

  /**
   * Session createManyAndReturn
   */
  export type SessionCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * The data used to create many Sessions.
     */
    data: SessionCreateManyInput | SessionCreateManyInput[]
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * Session update
   */
  export type SessionUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * The data needed to update a Session.
     */
    data: XOR<SessionUpdateInput, SessionUncheckedUpdateInput>
    /**
     * Choose, which Session to update.
     */
    where: SessionWhereUniqueInput
  }

  /**
   * Session updateMany
   */
  export type SessionUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Sessions.
     */
    data: XOR<SessionUpdateManyMutationInput, SessionUncheckedUpdateManyInput>
    /**
     * Filter which Sessions to update
     */
    where?: SessionWhereInput
    /**
     * Limit how many Sessions to update.
     */
    limit?: number
  }

  /**
   * Session updateManyAndReturn
   */
  export type SessionUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * The data used to update Sessions.
     */
    data: XOR<SessionUpdateManyMutationInput, SessionUncheckedUpdateManyInput>
    /**
     * Filter which Sessions to update
     */
    where?: SessionWhereInput
    /**
     * Limit how many Sessions to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * Session upsert
   */
  export type SessionUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * The filter to search for the Session to update in case it exists.
     */
    where: SessionWhereUniqueInput
    /**
     * In case the Session found by the `where` argument doesn't exist, create a new Session with this data.
     */
    create: XOR<SessionCreateInput, SessionUncheckedCreateInput>
    /**
     * In case the Session was found with the provided `where` argument, update it with this data.
     */
    update: XOR<SessionUpdateInput, SessionUncheckedUpdateInput>
  }

  /**
   * Session delete
   */
  export type SessionDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    /**
     * Filter which Session to delete.
     */
    where: SessionWhereUniqueInput
  }

  /**
   * Session deleteMany
   */
  export type SessionDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Sessions to delete
     */
    where?: SessionWhereInput
    /**
     * Limit how many Sessions to delete.
     */
    limit?: number
  }

  /**
   * Session without action
   */
  export type SessionDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
  }


  /**
   * Model User
   */

  export type AggregateUser = {
    _count: UserCountAggregateOutputType | null
    _min: UserMinAggregateOutputType | null
    _max: UserMaxAggregateOutputType | null
  }

  export type UserMinAggregateOutputType = {
    id: string | null
    name: string | null
    email: string | null
    emailVerified: Date | null
    image: string | null
  }

  export type UserMaxAggregateOutputType = {
    id: string | null
    name: string | null
    email: string | null
    emailVerified: Date | null
    image: string | null
  }

  export type UserCountAggregateOutputType = {
    id: number
    name: number
    email: number
    emailVerified: number
    image: number
    _all: number
  }


  export type UserMinAggregateInputType = {
    id?: true
    name?: true
    email?: true
    emailVerified?: true
    image?: true
  }

  export type UserMaxAggregateInputType = {
    id?: true
    name?: true
    email?: true
    emailVerified?: true
    image?: true
  }

  export type UserCountAggregateInputType = {
    id?: true
    name?: true
    email?: true
    emailVerified?: true
    image?: true
    _all?: true
  }

  export type UserAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which User to aggregate.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned Users
    **/
    _count?: true | UserCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: UserMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: UserMaxAggregateInputType
  }

  export type GetUserAggregateType<T extends UserAggregateArgs> = {
        [P in keyof T & keyof AggregateUser]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateUser[P]>
      : GetScalarType<T[P], AggregateUser[P]>
  }




  export type UserGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: UserWhereInput
    orderBy?: UserOrderByWithAggregationInput | UserOrderByWithAggregationInput[]
    by: UserScalarFieldEnum[] | UserScalarFieldEnum
    having?: UserScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: UserCountAggregateInputType | true
    _min?: UserMinAggregateInputType
    _max?: UserMaxAggregateInputType
  }

  export type UserGroupByOutputType = {
    id: string
    name: string | null
    email: string | null
    emailVerified: Date | null
    image: string | null
    _count: UserCountAggregateOutputType | null
    _min: UserMinAggregateOutputType | null
    _max: UserMaxAggregateOutputType | null
  }

  type GetUserGroupByPayload<T extends UserGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<UserGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof UserGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], UserGroupByOutputType[P]>
            : GetScalarType<T[P], UserGroupByOutputType[P]>
        }
      >
    >


  export type UserSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    name?: boolean
    email?: boolean
    emailVerified?: boolean
    image?: boolean
    accounts?: boolean | User$accountsArgs<ExtArgs>
    sessions?: boolean | User$sessionsArgs<ExtArgs>
    _count?: boolean | UserCountOutputTypeDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["user"]>

  export type UserSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    name?: boolean
    email?: boolean
    emailVerified?: boolean
    image?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    name?: boolean
    email?: boolean
    emailVerified?: boolean
    image?: boolean
  }, ExtArgs["result"]["user"]>

  export type UserSelectScalar = {
    id?: boolean
    name?: boolean
    email?: boolean
    emailVerified?: boolean
    image?: boolean
  }

  export type UserOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "name" | "email" | "emailVerified" | "image", ExtArgs["result"]["user"]>
  export type UserInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    accounts?: boolean | User$accountsArgs<ExtArgs>
    sessions?: boolean | User$sessionsArgs<ExtArgs>
    _count?: boolean | UserCountOutputTypeDefaultArgs<ExtArgs>
  }
  export type UserIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}
  export type UserIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}

  export type $UserPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "User"
    objects: {
      accounts: Prisma.$AccountPayload<ExtArgs>[]
      sessions: Prisma.$SessionPayload<ExtArgs>[]
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      name: string | null
      email: string | null
      emailVerified: Date | null
      image: string | null
    }, ExtArgs["result"]["user"]>
    composites: {}
  }

  type UserGetPayload<S extends boolean | null | undefined | UserDefaultArgs> = $Result.GetResult<Prisma.$UserPayload, S>

  type UserCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<UserFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: UserCountAggregateInputType | true
    }

  export interface UserDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['User'], meta: { name: 'User' } }
    /**
     * Find zero or one User that matches the filter.
     * @param {UserFindUniqueArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends UserFindUniqueArgs>(args: SelectSubset<T, UserFindUniqueArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one User that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {UserFindUniqueOrThrowArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends UserFindUniqueOrThrowArgs>(args: SelectSubset<T, UserFindUniqueOrThrowArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first User that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindFirstArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends UserFindFirstArgs>(args?: SelectSubset<T, UserFindFirstArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first User that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindFirstOrThrowArgs} args - Arguments to find a User
     * @example
     * // Get one User
     * const user = await prisma.user.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends UserFindFirstOrThrowArgs>(args?: SelectSubset<T, UserFindFirstOrThrowArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more Users that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all Users
     * const users = await prisma.user.findMany()
     * 
     * // Get first 10 Users
     * const users = await prisma.user.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const userWithIdOnly = await prisma.user.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends UserFindManyArgs>(args?: SelectSubset<T, UserFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a User.
     * @param {UserCreateArgs} args - Arguments to create a User.
     * @example
     * // Create one User
     * const User = await prisma.user.create({
     *   data: {
     *     // ... data to create a User
     *   }
     * })
     * 
     */
    create<T extends UserCreateArgs>(args: SelectSubset<T, UserCreateArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many Users.
     * @param {UserCreateManyArgs} args - Arguments to create many Users.
     * @example
     * // Create many Users
     * const user = await prisma.user.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends UserCreateManyArgs>(args?: SelectSubset<T, UserCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many Users and returns the data saved in the database.
     * @param {UserCreateManyAndReturnArgs} args - Arguments to create many Users.
     * @example
     * // Create many Users
     * const user = await prisma.user.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many Users and only return the `id`
     * const userWithIdOnly = await prisma.user.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends UserCreateManyAndReturnArgs>(args?: SelectSubset<T, UserCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a User.
     * @param {UserDeleteArgs} args - Arguments to delete one User.
     * @example
     * // Delete one User
     * const User = await prisma.user.delete({
     *   where: {
     *     // ... filter to delete one User
     *   }
     * })
     * 
     */
    delete<T extends UserDeleteArgs>(args: SelectSubset<T, UserDeleteArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one User.
     * @param {UserUpdateArgs} args - Arguments to update one User.
     * @example
     * // Update one User
     * const user = await prisma.user.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends UserUpdateArgs>(args: SelectSubset<T, UserUpdateArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more Users.
     * @param {UserDeleteManyArgs} args - Arguments to filter Users to delete.
     * @example
     * // Delete a few Users
     * const { count } = await prisma.user.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends UserDeleteManyArgs>(args?: SelectSubset<T, UserDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Users.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many Users
     * const user = await prisma.user.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends UserUpdateManyArgs>(args: SelectSubset<T, UserUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more Users and returns the data updated in the database.
     * @param {UserUpdateManyAndReturnArgs} args - Arguments to update many Users.
     * @example
     * // Update many Users
     * const user = await prisma.user.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more Users and only return the `id`
     * const userWithIdOnly = await prisma.user.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends UserUpdateManyAndReturnArgs>(args: SelectSubset<T, UserUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one User.
     * @param {UserUpsertArgs} args - Arguments to update or create a User.
     * @example
     * // Update or create a User
     * const user = await prisma.user.upsert({
     *   create: {
     *     // ... data to create a User
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the User we want to update
     *   }
     * })
     */
    upsert<T extends UserUpsertArgs>(args: SelectSubset<T, UserUpsertArgs<ExtArgs>>): Prisma__UserClient<$Result.GetResult<Prisma.$UserPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of Users.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserCountArgs} args - Arguments to filter Users to count.
     * @example
     * // Count the number of Users
     * const count = await prisma.user.count({
     *   where: {
     *     // ... the filter for the Users we want to count
     *   }
     * })
    **/
    count<T extends UserCountArgs>(
      args?: Subset<T, UserCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], UserCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a User.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends UserAggregateArgs>(args: Subset<T, UserAggregateArgs>): Prisma.PrismaPromise<GetUserAggregateType<T>>

    /**
     * Group by User.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {UserGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends UserGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: UserGroupByArgs['orderBy'] }
        : { orderBy?: UserGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, UserGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetUserGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the User model
   */
  readonly fields: UserFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for User.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__UserClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    accounts<T extends User$accountsArgs<ExtArgs> = {}>(args?: Subset<T, User$accountsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$AccountPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    sessions<T extends User$sessionsArgs<ExtArgs> = {}>(args?: Subset<T, User$sessionsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SessionPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the User model
   */
  interface UserFieldRefs {
    readonly id: FieldRef<"User", 'String'>
    readonly name: FieldRef<"User", 'String'>
    readonly email: FieldRef<"User", 'String'>
    readonly emailVerified: FieldRef<"User", 'DateTime'>
    readonly image: FieldRef<"User", 'String'>
  }
    

  // Custom InputTypes
  /**
   * User findUnique
   */
  export type UserFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User findUniqueOrThrow
   */
  export type UserFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User findFirst
   */
  export type UserFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Users.
     */
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User findFirstOrThrow
   */
  export type UserFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which User to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of Users.
     */
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User findMany
   */
  export type UserFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter, which Users to fetch.
     */
    where?: UserWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of Users to fetch.
     */
    orderBy?: UserOrderByWithRelationInput | UserOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing Users.
     */
    cursor?: UserWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` Users from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` Users.
     */
    skip?: number
    distinct?: UserScalarFieldEnum | UserScalarFieldEnum[]
  }

  /**
   * User create
   */
  export type UserCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * The data needed to create a User.
     */
    data?: XOR<UserCreateInput, UserUncheckedCreateInput>
  }

  /**
   * User createMany
   */
  export type UserCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many Users.
     */
    data: UserCreateManyInput | UserCreateManyInput[]
  }

  /**
   * User createManyAndReturn
   */
  export type UserCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data used to create many Users.
     */
    data: UserCreateManyInput | UserCreateManyInput[]
  }

  /**
   * User update
   */
  export type UserUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * The data needed to update a User.
     */
    data: XOR<UserUpdateInput, UserUncheckedUpdateInput>
    /**
     * Choose, which User to update.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User updateMany
   */
  export type UserUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update Users.
     */
    data: XOR<UserUpdateManyMutationInput, UserUncheckedUpdateManyInput>
    /**
     * Filter which Users to update
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to update.
     */
    limit?: number
  }

  /**
   * User updateManyAndReturn
   */
  export type UserUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * The data used to update Users.
     */
    data: XOR<UserUpdateManyMutationInput, UserUncheckedUpdateManyInput>
    /**
     * Filter which Users to update
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to update.
     */
    limit?: number
  }

  /**
   * User upsert
   */
  export type UserUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * The filter to search for the User to update in case it exists.
     */
    where: UserWhereUniqueInput
    /**
     * In case the User found by the `where` argument doesn't exist, create a new User with this data.
     */
    create: XOR<UserCreateInput, UserUncheckedCreateInput>
    /**
     * In case the User was found with the provided `where` argument, update it with this data.
     */
    update: XOR<UserUpdateInput, UserUncheckedUpdateInput>
  }

  /**
   * User delete
   */
  export type UserDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
    /**
     * Filter which User to delete.
     */
    where: UserWhereUniqueInput
  }

  /**
   * User deleteMany
   */
  export type UserDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which Users to delete
     */
    where?: UserWhereInput
    /**
     * Limit how many Users to delete.
     */
    limit?: number
  }

  /**
   * User.accounts
   */
  export type User$accountsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Account
     */
    select?: AccountSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Account
     */
    omit?: AccountOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: AccountInclude<ExtArgs> | null
    where?: AccountWhereInput
    orderBy?: AccountOrderByWithRelationInput | AccountOrderByWithRelationInput[]
    cursor?: AccountWhereUniqueInput
    take?: number
    skip?: number
    distinct?: AccountScalarFieldEnum | AccountScalarFieldEnum[]
  }

  /**
   * User.sessions
   */
  export type User$sessionsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the Session
     */
    select?: SessionSelect<ExtArgs> | null
    /**
     * Omit specific fields from the Session
     */
    omit?: SessionOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: SessionInclude<ExtArgs> | null
    where?: SessionWhereInput
    orderBy?: SessionOrderByWithRelationInput | SessionOrderByWithRelationInput[]
    cursor?: SessionWhereUniqueInput
    take?: number
    skip?: number
    distinct?: SessionScalarFieldEnum | SessionScalarFieldEnum[]
  }

  /**
   * User without action
   */
  export type UserDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the User
     */
    select?: UserSelect<ExtArgs> | null
    /**
     * Omit specific fields from the User
     */
    omit?: UserOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: UserInclude<ExtArgs> | null
  }


  /**
   * Model VerificationToken
   */

  export type AggregateVerificationToken = {
    _count: VerificationTokenCountAggregateOutputType | null
    _min: VerificationTokenMinAggregateOutputType | null
    _max: VerificationTokenMaxAggregateOutputType | null
  }

  export type VerificationTokenMinAggregateOutputType = {
    identifier: string | null
    token: string | null
    expires: Date | null
  }

  export type VerificationTokenMaxAggregateOutputType = {
    identifier: string | null
    token: string | null
    expires: Date | null
  }

  export type VerificationTokenCountAggregateOutputType = {
    identifier: number
    token: number
    expires: number
    _all: number
  }


  export type VerificationTokenMinAggregateInputType = {
    identifier?: true
    token?: true
    expires?: true
  }

  export type VerificationTokenMaxAggregateInputType = {
    identifier?: true
    token?: true
    expires?: true
  }

  export type VerificationTokenCountAggregateInputType = {
    identifier?: true
    token?: true
    expires?: true
    _all?: true
  }

  export type VerificationTokenAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which VerificationToken to aggregate.
     */
    where?: VerificationTokenWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VerificationTokens to fetch.
     */
    orderBy?: VerificationTokenOrderByWithRelationInput | VerificationTokenOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: VerificationTokenWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VerificationTokens from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VerificationTokens.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned VerificationTokens
    **/
    _count?: true | VerificationTokenCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: VerificationTokenMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: VerificationTokenMaxAggregateInputType
  }

  export type GetVerificationTokenAggregateType<T extends VerificationTokenAggregateArgs> = {
        [P in keyof T & keyof AggregateVerificationToken]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateVerificationToken[P]>
      : GetScalarType<T[P], AggregateVerificationToken[P]>
  }




  export type VerificationTokenGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: VerificationTokenWhereInput
    orderBy?: VerificationTokenOrderByWithAggregationInput | VerificationTokenOrderByWithAggregationInput[]
    by: VerificationTokenScalarFieldEnum[] | VerificationTokenScalarFieldEnum
    having?: VerificationTokenScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: VerificationTokenCountAggregateInputType | true
    _min?: VerificationTokenMinAggregateInputType
    _max?: VerificationTokenMaxAggregateInputType
  }

  export type VerificationTokenGroupByOutputType = {
    identifier: string
    token: string
    expires: Date
    _count: VerificationTokenCountAggregateOutputType | null
    _min: VerificationTokenMinAggregateOutputType | null
    _max: VerificationTokenMaxAggregateOutputType | null
  }

  type GetVerificationTokenGroupByPayload<T extends VerificationTokenGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<VerificationTokenGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof VerificationTokenGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], VerificationTokenGroupByOutputType[P]>
            : GetScalarType<T[P], VerificationTokenGroupByOutputType[P]>
        }
      >
    >


  export type VerificationTokenSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    identifier?: boolean
    token?: boolean
    expires?: boolean
  }, ExtArgs["result"]["verificationToken"]>

  export type VerificationTokenSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    identifier?: boolean
    token?: boolean
    expires?: boolean
  }, ExtArgs["result"]["verificationToken"]>

  export type VerificationTokenSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    identifier?: boolean
    token?: boolean
    expires?: boolean
  }, ExtArgs["result"]["verificationToken"]>

  export type VerificationTokenSelectScalar = {
    identifier?: boolean
    token?: boolean
    expires?: boolean
  }

  export type VerificationTokenOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"identifier" | "token" | "expires", ExtArgs["result"]["verificationToken"]>

  export type $VerificationTokenPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "VerificationToken"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      identifier: string
      token: string
      expires: Date
    }, ExtArgs["result"]["verificationToken"]>
    composites: {}
  }

  type VerificationTokenGetPayload<S extends boolean | null | undefined | VerificationTokenDefaultArgs> = $Result.GetResult<Prisma.$VerificationTokenPayload, S>

  type VerificationTokenCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<VerificationTokenFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: VerificationTokenCountAggregateInputType | true
    }

  export interface VerificationTokenDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['VerificationToken'], meta: { name: 'VerificationToken' } }
    /**
     * Find zero or one VerificationToken that matches the filter.
     * @param {VerificationTokenFindUniqueArgs} args - Arguments to find a VerificationToken
     * @example
     * // Get one VerificationToken
     * const verificationToken = await prisma.verificationToken.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends VerificationTokenFindUniqueArgs>(args: SelectSubset<T, VerificationTokenFindUniqueArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one VerificationToken that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {VerificationTokenFindUniqueOrThrowArgs} args - Arguments to find a VerificationToken
     * @example
     * // Get one VerificationToken
     * const verificationToken = await prisma.verificationToken.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends VerificationTokenFindUniqueOrThrowArgs>(args: SelectSubset<T, VerificationTokenFindUniqueOrThrowArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first VerificationToken that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenFindFirstArgs} args - Arguments to find a VerificationToken
     * @example
     * // Get one VerificationToken
     * const verificationToken = await prisma.verificationToken.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends VerificationTokenFindFirstArgs>(args?: SelectSubset<T, VerificationTokenFindFirstArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first VerificationToken that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenFindFirstOrThrowArgs} args - Arguments to find a VerificationToken
     * @example
     * // Get one VerificationToken
     * const verificationToken = await prisma.verificationToken.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends VerificationTokenFindFirstOrThrowArgs>(args?: SelectSubset<T, VerificationTokenFindFirstOrThrowArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more VerificationTokens that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all VerificationTokens
     * const verificationTokens = await prisma.verificationToken.findMany()
     * 
     * // Get first 10 VerificationTokens
     * const verificationTokens = await prisma.verificationToken.findMany({ take: 10 })
     * 
     * // Only select the `identifier`
     * const verificationTokenWithIdentifierOnly = await prisma.verificationToken.findMany({ select: { identifier: true } })
     * 
     */
    findMany<T extends VerificationTokenFindManyArgs>(args?: SelectSubset<T, VerificationTokenFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a VerificationToken.
     * @param {VerificationTokenCreateArgs} args - Arguments to create a VerificationToken.
     * @example
     * // Create one VerificationToken
     * const VerificationToken = await prisma.verificationToken.create({
     *   data: {
     *     // ... data to create a VerificationToken
     *   }
     * })
     * 
     */
    create<T extends VerificationTokenCreateArgs>(args: SelectSubset<T, VerificationTokenCreateArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many VerificationTokens.
     * @param {VerificationTokenCreateManyArgs} args - Arguments to create many VerificationTokens.
     * @example
     * // Create many VerificationTokens
     * const verificationToken = await prisma.verificationToken.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends VerificationTokenCreateManyArgs>(args?: SelectSubset<T, VerificationTokenCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many VerificationTokens and returns the data saved in the database.
     * @param {VerificationTokenCreateManyAndReturnArgs} args - Arguments to create many VerificationTokens.
     * @example
     * // Create many VerificationTokens
     * const verificationToken = await prisma.verificationToken.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many VerificationTokens and only return the `identifier`
     * const verificationTokenWithIdentifierOnly = await prisma.verificationToken.createManyAndReturn({
     *   select: { identifier: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends VerificationTokenCreateManyAndReturnArgs>(args?: SelectSubset<T, VerificationTokenCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a VerificationToken.
     * @param {VerificationTokenDeleteArgs} args - Arguments to delete one VerificationToken.
     * @example
     * // Delete one VerificationToken
     * const VerificationToken = await prisma.verificationToken.delete({
     *   where: {
     *     // ... filter to delete one VerificationToken
     *   }
     * })
     * 
     */
    delete<T extends VerificationTokenDeleteArgs>(args: SelectSubset<T, VerificationTokenDeleteArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one VerificationToken.
     * @param {VerificationTokenUpdateArgs} args - Arguments to update one VerificationToken.
     * @example
     * // Update one VerificationToken
     * const verificationToken = await prisma.verificationToken.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends VerificationTokenUpdateArgs>(args: SelectSubset<T, VerificationTokenUpdateArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more VerificationTokens.
     * @param {VerificationTokenDeleteManyArgs} args - Arguments to filter VerificationTokens to delete.
     * @example
     * // Delete a few VerificationTokens
     * const { count } = await prisma.verificationToken.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends VerificationTokenDeleteManyArgs>(args?: SelectSubset<T, VerificationTokenDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more VerificationTokens.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many VerificationTokens
     * const verificationToken = await prisma.verificationToken.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends VerificationTokenUpdateManyArgs>(args: SelectSubset<T, VerificationTokenUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more VerificationTokens and returns the data updated in the database.
     * @param {VerificationTokenUpdateManyAndReturnArgs} args - Arguments to update many VerificationTokens.
     * @example
     * // Update many VerificationTokens
     * const verificationToken = await prisma.verificationToken.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more VerificationTokens and only return the `identifier`
     * const verificationTokenWithIdentifierOnly = await prisma.verificationToken.updateManyAndReturn({
     *   select: { identifier: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends VerificationTokenUpdateManyAndReturnArgs>(args: SelectSubset<T, VerificationTokenUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one VerificationToken.
     * @param {VerificationTokenUpsertArgs} args - Arguments to update or create a VerificationToken.
     * @example
     * // Update or create a VerificationToken
     * const verificationToken = await prisma.verificationToken.upsert({
     *   create: {
     *     // ... data to create a VerificationToken
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the VerificationToken we want to update
     *   }
     * })
     */
    upsert<T extends VerificationTokenUpsertArgs>(args: SelectSubset<T, VerificationTokenUpsertArgs<ExtArgs>>): Prisma__VerificationTokenClient<$Result.GetResult<Prisma.$VerificationTokenPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of VerificationTokens.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenCountArgs} args - Arguments to filter VerificationTokens to count.
     * @example
     * // Count the number of VerificationTokens
     * const count = await prisma.verificationToken.count({
     *   where: {
     *     // ... the filter for the VerificationTokens we want to count
     *   }
     * })
    **/
    count<T extends VerificationTokenCountArgs>(
      args?: Subset<T, VerificationTokenCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], VerificationTokenCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a VerificationToken.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends VerificationTokenAggregateArgs>(args: Subset<T, VerificationTokenAggregateArgs>): Prisma.PrismaPromise<GetVerificationTokenAggregateType<T>>

    /**
     * Group by VerificationToken.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {VerificationTokenGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends VerificationTokenGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: VerificationTokenGroupByArgs['orderBy'] }
        : { orderBy?: VerificationTokenGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, VerificationTokenGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetVerificationTokenGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the VerificationToken model
   */
  readonly fields: VerificationTokenFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for VerificationToken.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__VerificationTokenClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the VerificationToken model
   */
  interface VerificationTokenFieldRefs {
    readonly identifier: FieldRef<"VerificationToken", 'String'>
    readonly token: FieldRef<"VerificationToken", 'String'>
    readonly expires: FieldRef<"VerificationToken", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * VerificationToken findUnique
   */
  export type VerificationTokenFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * Filter, which VerificationToken to fetch.
     */
    where: VerificationTokenWhereUniqueInput
  }

  /**
   * VerificationToken findUniqueOrThrow
   */
  export type VerificationTokenFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * Filter, which VerificationToken to fetch.
     */
    where: VerificationTokenWhereUniqueInput
  }

  /**
   * VerificationToken findFirst
   */
  export type VerificationTokenFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * Filter, which VerificationToken to fetch.
     */
    where?: VerificationTokenWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VerificationTokens to fetch.
     */
    orderBy?: VerificationTokenOrderByWithRelationInput | VerificationTokenOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for VerificationTokens.
     */
    cursor?: VerificationTokenWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VerificationTokens from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VerificationTokens.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of VerificationTokens.
     */
    distinct?: VerificationTokenScalarFieldEnum | VerificationTokenScalarFieldEnum[]
  }

  /**
   * VerificationToken findFirstOrThrow
   */
  export type VerificationTokenFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * Filter, which VerificationToken to fetch.
     */
    where?: VerificationTokenWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VerificationTokens to fetch.
     */
    orderBy?: VerificationTokenOrderByWithRelationInput | VerificationTokenOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for VerificationTokens.
     */
    cursor?: VerificationTokenWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VerificationTokens from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VerificationTokens.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of VerificationTokens.
     */
    distinct?: VerificationTokenScalarFieldEnum | VerificationTokenScalarFieldEnum[]
  }

  /**
   * VerificationToken findMany
   */
  export type VerificationTokenFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * Filter, which VerificationTokens to fetch.
     */
    where?: VerificationTokenWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of VerificationTokens to fetch.
     */
    orderBy?: VerificationTokenOrderByWithRelationInput | VerificationTokenOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing VerificationTokens.
     */
    cursor?: VerificationTokenWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` VerificationTokens from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` VerificationTokens.
     */
    skip?: number
    distinct?: VerificationTokenScalarFieldEnum | VerificationTokenScalarFieldEnum[]
  }

  /**
   * VerificationToken create
   */
  export type VerificationTokenCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * The data needed to create a VerificationToken.
     */
    data: XOR<VerificationTokenCreateInput, VerificationTokenUncheckedCreateInput>
  }

  /**
   * VerificationToken createMany
   */
  export type VerificationTokenCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many VerificationTokens.
     */
    data: VerificationTokenCreateManyInput | VerificationTokenCreateManyInput[]
  }

  /**
   * VerificationToken createManyAndReturn
   */
  export type VerificationTokenCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * The data used to create many VerificationTokens.
     */
    data: VerificationTokenCreateManyInput | VerificationTokenCreateManyInput[]
  }

  /**
   * VerificationToken update
   */
  export type VerificationTokenUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * The data needed to update a VerificationToken.
     */
    data: XOR<VerificationTokenUpdateInput, VerificationTokenUncheckedUpdateInput>
    /**
     * Choose, which VerificationToken to update.
     */
    where: VerificationTokenWhereUniqueInput
  }

  /**
   * VerificationToken updateMany
   */
  export type VerificationTokenUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update VerificationTokens.
     */
    data: XOR<VerificationTokenUpdateManyMutationInput, VerificationTokenUncheckedUpdateManyInput>
    /**
     * Filter which VerificationTokens to update
     */
    where?: VerificationTokenWhereInput
    /**
     * Limit how many VerificationTokens to update.
     */
    limit?: number
  }

  /**
   * VerificationToken updateManyAndReturn
   */
  export type VerificationTokenUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * The data used to update VerificationTokens.
     */
    data: XOR<VerificationTokenUpdateManyMutationInput, VerificationTokenUncheckedUpdateManyInput>
    /**
     * Filter which VerificationTokens to update
     */
    where?: VerificationTokenWhereInput
    /**
     * Limit how many VerificationTokens to update.
     */
    limit?: number
  }

  /**
   * VerificationToken upsert
   */
  export type VerificationTokenUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * The filter to search for the VerificationToken to update in case it exists.
     */
    where: VerificationTokenWhereUniqueInput
    /**
     * In case the VerificationToken found by the `where` argument doesn't exist, create a new VerificationToken with this data.
     */
    create: XOR<VerificationTokenCreateInput, VerificationTokenUncheckedCreateInput>
    /**
     * In case the VerificationToken was found with the provided `where` argument, update it with this data.
     */
    update: XOR<VerificationTokenUpdateInput, VerificationTokenUncheckedUpdateInput>
  }

  /**
   * VerificationToken delete
   */
  export type VerificationTokenDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
    /**
     * Filter which VerificationToken to delete.
     */
    where: VerificationTokenWhereUniqueInput
  }

  /**
   * VerificationToken deleteMany
   */
  export type VerificationTokenDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which VerificationTokens to delete
     */
    where?: VerificationTokenWhereInput
    /**
     * Limit how many VerificationTokens to delete.
     */
    limit?: number
  }

  /**
   * VerificationToken without action
   */
  export type VerificationTokenDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the VerificationToken
     */
    select?: VerificationTokenSelect<ExtArgs> | null
    /**
     * Omit specific fields from the VerificationToken
     */
    omit?: VerificationTokenOmit<ExtArgs> | null
  }


  /**
   * Model EmailVerificationRequest
   */

  export type AggregateEmailVerificationRequest = {
    _count: EmailVerificationRequestCountAggregateOutputType | null
    _min: EmailVerificationRequestMinAggregateOutputType | null
    _max: EmailVerificationRequestMaxAggregateOutputType | null
  }

  export type EmailVerificationRequestMinAggregateOutputType = {
    id: string | null
    email: string | null
    createdAt: Date | null
    invalidated: boolean | null
  }

  export type EmailVerificationRequestMaxAggregateOutputType = {
    id: string | null
    email: string | null
    createdAt: Date | null
    invalidated: boolean | null
  }

  export type EmailVerificationRequestCountAggregateOutputType = {
    id: number
    email: number
    createdAt: number
    invalidated: number
    _all: number
  }


  export type EmailVerificationRequestMinAggregateInputType = {
    id?: true
    email?: true
    createdAt?: true
    invalidated?: true
  }

  export type EmailVerificationRequestMaxAggregateInputType = {
    id?: true
    email?: true
    createdAt?: true
    invalidated?: true
  }

  export type EmailVerificationRequestCountAggregateInputType = {
    id?: true
    email?: true
    createdAt?: true
    invalidated?: true
    _all?: true
  }

  export type EmailVerificationRequestAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which EmailVerificationRequest to aggregate.
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of EmailVerificationRequests to fetch.
     */
    orderBy?: EmailVerificationRequestOrderByWithRelationInput | EmailVerificationRequestOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: EmailVerificationRequestWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` EmailVerificationRequests from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` EmailVerificationRequests.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned EmailVerificationRequests
    **/
    _count?: true | EmailVerificationRequestCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: EmailVerificationRequestMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: EmailVerificationRequestMaxAggregateInputType
  }

  export type GetEmailVerificationRequestAggregateType<T extends EmailVerificationRequestAggregateArgs> = {
        [P in keyof T & keyof AggregateEmailVerificationRequest]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateEmailVerificationRequest[P]>
      : GetScalarType<T[P], AggregateEmailVerificationRequest[P]>
  }




  export type EmailVerificationRequestGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: EmailVerificationRequestWhereInput
    orderBy?: EmailVerificationRequestOrderByWithAggregationInput | EmailVerificationRequestOrderByWithAggregationInput[]
    by: EmailVerificationRequestScalarFieldEnum[] | EmailVerificationRequestScalarFieldEnum
    having?: EmailVerificationRequestScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: EmailVerificationRequestCountAggregateInputType | true
    _min?: EmailVerificationRequestMinAggregateInputType
    _max?: EmailVerificationRequestMaxAggregateInputType
  }

  export type EmailVerificationRequestGroupByOutputType = {
    id: string
    email: string
    createdAt: Date
    invalidated: boolean
    _count: EmailVerificationRequestCountAggregateOutputType | null
    _min: EmailVerificationRequestMinAggregateOutputType | null
    _max: EmailVerificationRequestMaxAggregateOutputType | null
  }

  type GetEmailVerificationRequestGroupByPayload<T extends EmailVerificationRequestGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<EmailVerificationRequestGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof EmailVerificationRequestGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], EmailVerificationRequestGroupByOutputType[P]>
            : GetScalarType<T[P], EmailVerificationRequestGroupByOutputType[P]>
        }
      >
    >


  export type EmailVerificationRequestSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    email?: boolean
    createdAt?: boolean
    invalidated?: boolean
  }, ExtArgs["result"]["emailVerificationRequest"]>

  export type EmailVerificationRequestSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    email?: boolean
    createdAt?: boolean
    invalidated?: boolean
  }, ExtArgs["result"]["emailVerificationRequest"]>

  export type EmailVerificationRequestSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    email?: boolean
    createdAt?: boolean
    invalidated?: boolean
  }, ExtArgs["result"]["emailVerificationRequest"]>

  export type EmailVerificationRequestSelectScalar = {
    id?: boolean
    email?: boolean
    createdAt?: boolean
    invalidated?: boolean
  }

  export type EmailVerificationRequestOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "email" | "createdAt" | "invalidated", ExtArgs["result"]["emailVerificationRequest"]>

  export type $EmailVerificationRequestPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "EmailVerificationRequest"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      id: string
      email: string
      createdAt: Date
      invalidated: boolean
    }, ExtArgs["result"]["emailVerificationRequest"]>
    composites: {}
  }

  type EmailVerificationRequestGetPayload<S extends boolean | null | undefined | EmailVerificationRequestDefaultArgs> = $Result.GetResult<Prisma.$EmailVerificationRequestPayload, S>

  type EmailVerificationRequestCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<EmailVerificationRequestFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: EmailVerificationRequestCountAggregateInputType | true
    }

  export interface EmailVerificationRequestDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['EmailVerificationRequest'], meta: { name: 'EmailVerificationRequest' } }
    /**
     * Find zero or one EmailVerificationRequest that matches the filter.
     * @param {EmailVerificationRequestFindUniqueArgs} args - Arguments to find a EmailVerificationRequest
     * @example
     * // Get one EmailVerificationRequest
     * const emailVerificationRequest = await prisma.emailVerificationRequest.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends EmailVerificationRequestFindUniqueArgs>(args: SelectSubset<T, EmailVerificationRequestFindUniqueArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one EmailVerificationRequest that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {EmailVerificationRequestFindUniqueOrThrowArgs} args - Arguments to find a EmailVerificationRequest
     * @example
     * // Get one EmailVerificationRequest
     * const emailVerificationRequest = await prisma.emailVerificationRequest.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends EmailVerificationRequestFindUniqueOrThrowArgs>(args: SelectSubset<T, EmailVerificationRequestFindUniqueOrThrowArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first EmailVerificationRequest that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestFindFirstArgs} args - Arguments to find a EmailVerificationRequest
     * @example
     * // Get one EmailVerificationRequest
     * const emailVerificationRequest = await prisma.emailVerificationRequest.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends EmailVerificationRequestFindFirstArgs>(args?: SelectSubset<T, EmailVerificationRequestFindFirstArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first EmailVerificationRequest that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestFindFirstOrThrowArgs} args - Arguments to find a EmailVerificationRequest
     * @example
     * // Get one EmailVerificationRequest
     * const emailVerificationRequest = await prisma.emailVerificationRequest.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends EmailVerificationRequestFindFirstOrThrowArgs>(args?: SelectSubset<T, EmailVerificationRequestFindFirstOrThrowArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more EmailVerificationRequests that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all EmailVerificationRequests
     * const emailVerificationRequests = await prisma.emailVerificationRequest.findMany()
     * 
     * // Get first 10 EmailVerificationRequests
     * const emailVerificationRequests = await prisma.emailVerificationRequest.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const emailVerificationRequestWithIdOnly = await prisma.emailVerificationRequest.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends EmailVerificationRequestFindManyArgs>(args?: SelectSubset<T, EmailVerificationRequestFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a EmailVerificationRequest.
     * @param {EmailVerificationRequestCreateArgs} args - Arguments to create a EmailVerificationRequest.
     * @example
     * // Create one EmailVerificationRequest
     * const EmailVerificationRequest = await prisma.emailVerificationRequest.create({
     *   data: {
     *     // ... data to create a EmailVerificationRequest
     *   }
     * })
     * 
     */
    create<T extends EmailVerificationRequestCreateArgs>(args: SelectSubset<T, EmailVerificationRequestCreateArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many EmailVerificationRequests.
     * @param {EmailVerificationRequestCreateManyArgs} args - Arguments to create many EmailVerificationRequests.
     * @example
     * // Create many EmailVerificationRequests
     * const emailVerificationRequest = await prisma.emailVerificationRequest.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends EmailVerificationRequestCreateManyArgs>(args?: SelectSubset<T, EmailVerificationRequestCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many EmailVerificationRequests and returns the data saved in the database.
     * @param {EmailVerificationRequestCreateManyAndReturnArgs} args - Arguments to create many EmailVerificationRequests.
     * @example
     * // Create many EmailVerificationRequests
     * const emailVerificationRequest = await prisma.emailVerificationRequest.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many EmailVerificationRequests and only return the `id`
     * const emailVerificationRequestWithIdOnly = await prisma.emailVerificationRequest.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends EmailVerificationRequestCreateManyAndReturnArgs>(args?: SelectSubset<T, EmailVerificationRequestCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a EmailVerificationRequest.
     * @param {EmailVerificationRequestDeleteArgs} args - Arguments to delete one EmailVerificationRequest.
     * @example
     * // Delete one EmailVerificationRequest
     * const EmailVerificationRequest = await prisma.emailVerificationRequest.delete({
     *   where: {
     *     // ... filter to delete one EmailVerificationRequest
     *   }
     * })
     * 
     */
    delete<T extends EmailVerificationRequestDeleteArgs>(args: SelectSubset<T, EmailVerificationRequestDeleteArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one EmailVerificationRequest.
     * @param {EmailVerificationRequestUpdateArgs} args - Arguments to update one EmailVerificationRequest.
     * @example
     * // Update one EmailVerificationRequest
     * const emailVerificationRequest = await prisma.emailVerificationRequest.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends EmailVerificationRequestUpdateArgs>(args: SelectSubset<T, EmailVerificationRequestUpdateArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more EmailVerificationRequests.
     * @param {EmailVerificationRequestDeleteManyArgs} args - Arguments to filter EmailVerificationRequests to delete.
     * @example
     * // Delete a few EmailVerificationRequests
     * const { count } = await prisma.emailVerificationRequest.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends EmailVerificationRequestDeleteManyArgs>(args?: SelectSubset<T, EmailVerificationRequestDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more EmailVerificationRequests.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many EmailVerificationRequests
     * const emailVerificationRequest = await prisma.emailVerificationRequest.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends EmailVerificationRequestUpdateManyArgs>(args: SelectSubset<T, EmailVerificationRequestUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more EmailVerificationRequests and returns the data updated in the database.
     * @param {EmailVerificationRequestUpdateManyAndReturnArgs} args - Arguments to update many EmailVerificationRequests.
     * @example
     * // Update many EmailVerificationRequests
     * const emailVerificationRequest = await prisma.emailVerificationRequest.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more EmailVerificationRequests and only return the `id`
     * const emailVerificationRequestWithIdOnly = await prisma.emailVerificationRequest.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends EmailVerificationRequestUpdateManyAndReturnArgs>(args: SelectSubset<T, EmailVerificationRequestUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one EmailVerificationRequest.
     * @param {EmailVerificationRequestUpsertArgs} args - Arguments to update or create a EmailVerificationRequest.
     * @example
     * // Update or create a EmailVerificationRequest
     * const emailVerificationRequest = await prisma.emailVerificationRequest.upsert({
     *   create: {
     *     // ... data to create a EmailVerificationRequest
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the EmailVerificationRequest we want to update
     *   }
     * })
     */
    upsert<T extends EmailVerificationRequestUpsertArgs>(args: SelectSubset<T, EmailVerificationRequestUpsertArgs<ExtArgs>>): Prisma__EmailVerificationRequestClient<$Result.GetResult<Prisma.$EmailVerificationRequestPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of EmailVerificationRequests.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestCountArgs} args - Arguments to filter EmailVerificationRequests to count.
     * @example
     * // Count the number of EmailVerificationRequests
     * const count = await prisma.emailVerificationRequest.count({
     *   where: {
     *     // ... the filter for the EmailVerificationRequests we want to count
     *   }
     * })
    **/
    count<T extends EmailVerificationRequestCountArgs>(
      args?: Subset<T, EmailVerificationRequestCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], EmailVerificationRequestCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a EmailVerificationRequest.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends EmailVerificationRequestAggregateArgs>(args: Subset<T, EmailVerificationRequestAggregateArgs>): Prisma.PrismaPromise<GetEmailVerificationRequestAggregateType<T>>

    /**
     * Group by EmailVerificationRequest.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {EmailVerificationRequestGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends EmailVerificationRequestGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: EmailVerificationRequestGroupByArgs['orderBy'] }
        : { orderBy?: EmailVerificationRequestGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, EmailVerificationRequestGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetEmailVerificationRequestGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the EmailVerificationRequest model
   */
  readonly fields: EmailVerificationRequestFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for EmailVerificationRequest.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__EmailVerificationRequestClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the EmailVerificationRequest model
   */
  interface EmailVerificationRequestFieldRefs {
    readonly id: FieldRef<"EmailVerificationRequest", 'String'>
    readonly email: FieldRef<"EmailVerificationRequest", 'String'>
    readonly createdAt: FieldRef<"EmailVerificationRequest", 'DateTime'>
    readonly invalidated: FieldRef<"EmailVerificationRequest", 'Boolean'>
  }
    

  // Custom InputTypes
  /**
   * EmailVerificationRequest findUnique
   */
  export type EmailVerificationRequestFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * Filter, which EmailVerificationRequest to fetch.
     */
    where: EmailVerificationRequestWhereUniqueInput
  }

  /**
   * EmailVerificationRequest findUniqueOrThrow
   */
  export type EmailVerificationRequestFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * Filter, which EmailVerificationRequest to fetch.
     */
    where: EmailVerificationRequestWhereUniqueInput
  }

  /**
   * EmailVerificationRequest findFirst
   */
  export type EmailVerificationRequestFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * Filter, which EmailVerificationRequest to fetch.
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of EmailVerificationRequests to fetch.
     */
    orderBy?: EmailVerificationRequestOrderByWithRelationInput | EmailVerificationRequestOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for EmailVerificationRequests.
     */
    cursor?: EmailVerificationRequestWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` EmailVerificationRequests from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` EmailVerificationRequests.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of EmailVerificationRequests.
     */
    distinct?: EmailVerificationRequestScalarFieldEnum | EmailVerificationRequestScalarFieldEnum[]
  }

  /**
   * EmailVerificationRequest findFirstOrThrow
   */
  export type EmailVerificationRequestFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * Filter, which EmailVerificationRequest to fetch.
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of EmailVerificationRequests to fetch.
     */
    orderBy?: EmailVerificationRequestOrderByWithRelationInput | EmailVerificationRequestOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for EmailVerificationRequests.
     */
    cursor?: EmailVerificationRequestWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` EmailVerificationRequests from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` EmailVerificationRequests.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of EmailVerificationRequests.
     */
    distinct?: EmailVerificationRequestScalarFieldEnum | EmailVerificationRequestScalarFieldEnum[]
  }

  /**
   * EmailVerificationRequest findMany
   */
  export type EmailVerificationRequestFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * Filter, which EmailVerificationRequests to fetch.
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of EmailVerificationRequests to fetch.
     */
    orderBy?: EmailVerificationRequestOrderByWithRelationInput | EmailVerificationRequestOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing EmailVerificationRequests.
     */
    cursor?: EmailVerificationRequestWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` EmailVerificationRequests from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` EmailVerificationRequests.
     */
    skip?: number
    distinct?: EmailVerificationRequestScalarFieldEnum | EmailVerificationRequestScalarFieldEnum[]
  }

  /**
   * EmailVerificationRequest create
   */
  export type EmailVerificationRequestCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * The data needed to create a EmailVerificationRequest.
     */
    data: XOR<EmailVerificationRequestCreateInput, EmailVerificationRequestUncheckedCreateInput>
  }

  /**
   * EmailVerificationRequest createMany
   */
  export type EmailVerificationRequestCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many EmailVerificationRequests.
     */
    data: EmailVerificationRequestCreateManyInput | EmailVerificationRequestCreateManyInput[]
  }

  /**
   * EmailVerificationRequest createManyAndReturn
   */
  export type EmailVerificationRequestCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * The data used to create many EmailVerificationRequests.
     */
    data: EmailVerificationRequestCreateManyInput | EmailVerificationRequestCreateManyInput[]
  }

  /**
   * EmailVerificationRequest update
   */
  export type EmailVerificationRequestUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * The data needed to update a EmailVerificationRequest.
     */
    data: XOR<EmailVerificationRequestUpdateInput, EmailVerificationRequestUncheckedUpdateInput>
    /**
     * Choose, which EmailVerificationRequest to update.
     */
    where: EmailVerificationRequestWhereUniqueInput
  }

  /**
   * EmailVerificationRequest updateMany
   */
  export type EmailVerificationRequestUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update EmailVerificationRequests.
     */
    data: XOR<EmailVerificationRequestUpdateManyMutationInput, EmailVerificationRequestUncheckedUpdateManyInput>
    /**
     * Filter which EmailVerificationRequests to update
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * Limit how many EmailVerificationRequests to update.
     */
    limit?: number
  }

  /**
   * EmailVerificationRequest updateManyAndReturn
   */
  export type EmailVerificationRequestUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * The data used to update EmailVerificationRequests.
     */
    data: XOR<EmailVerificationRequestUpdateManyMutationInput, EmailVerificationRequestUncheckedUpdateManyInput>
    /**
     * Filter which EmailVerificationRequests to update
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * Limit how many EmailVerificationRequests to update.
     */
    limit?: number
  }

  /**
   * EmailVerificationRequest upsert
   */
  export type EmailVerificationRequestUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * The filter to search for the EmailVerificationRequest to update in case it exists.
     */
    where: EmailVerificationRequestWhereUniqueInput
    /**
     * In case the EmailVerificationRequest found by the `where` argument doesn't exist, create a new EmailVerificationRequest with this data.
     */
    create: XOR<EmailVerificationRequestCreateInput, EmailVerificationRequestUncheckedCreateInput>
    /**
     * In case the EmailVerificationRequest was found with the provided `where` argument, update it with this data.
     */
    update: XOR<EmailVerificationRequestUpdateInput, EmailVerificationRequestUncheckedUpdateInput>
  }

  /**
   * EmailVerificationRequest delete
   */
  export type EmailVerificationRequestDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
    /**
     * Filter which EmailVerificationRequest to delete.
     */
    where: EmailVerificationRequestWhereUniqueInput
  }

  /**
   * EmailVerificationRequest deleteMany
   */
  export type EmailVerificationRequestDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which EmailVerificationRequests to delete
     */
    where?: EmailVerificationRequestWhereInput
    /**
     * Limit how many EmailVerificationRequests to delete.
     */
    limit?: number
  }

  /**
   * EmailVerificationRequest without action
   */
  export type EmailVerificationRequestDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the EmailVerificationRequest
     */
    select?: EmailVerificationRequestSelect<ExtArgs> | null
    /**
     * Omit specific fields from the EmailVerificationRequest
     */
    omit?: EmailVerificationRequestOmit<ExtArgs> | null
  }


  /**
   * Model LocalUserProfile
   */

  export type AggregateLocalUserProfile = {
    _count: LocalUserProfileCountAggregateOutputType | null
    _min: LocalUserProfileMinAggregateOutputType | null
    _max: LocalUserProfileMaxAggregateOutputType | null
  }

  export type LocalUserProfileMinAggregateOutputType = {
    id: string | null
    userId: string | null
    publicId: string | null
    email: string | null
    name: string | null
    hasCompletedOnboarding: boolean | null
    topics: string | null
    topicsDetails: string | null
    regions: string | null
    languages: string | null
    publications: string | null
    lastSyncAt: Date | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type LocalUserProfileMaxAggregateOutputType = {
    id: string | null
    userId: string | null
    publicId: string | null
    email: string | null
    name: string | null
    hasCompletedOnboarding: boolean | null
    topics: string | null
    topicsDetails: string | null
    regions: string | null
    languages: string | null
    publications: string | null
    lastSyncAt: Date | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type LocalUserProfileCountAggregateOutputType = {
    id: number
    userId: number
    publicId: number
    email: number
    name: number
    hasCompletedOnboarding: number
    topics: number
    topicsDetails: number
    regions: number
    languages: number
    publications: number
    lastSyncAt: number
    createdAt: number
    updatedAt: number
    _all: number
  }


  export type LocalUserProfileMinAggregateInputType = {
    id?: true
    userId?: true
    publicId?: true
    email?: true
    name?: true
    hasCompletedOnboarding?: true
    topics?: true
    topicsDetails?: true
    regions?: true
    languages?: true
    publications?: true
    lastSyncAt?: true
    createdAt?: true
    updatedAt?: true
  }

  export type LocalUserProfileMaxAggregateInputType = {
    id?: true
    userId?: true
    publicId?: true
    email?: true
    name?: true
    hasCompletedOnboarding?: true
    topics?: true
    topicsDetails?: true
    regions?: true
    languages?: true
    publications?: true
    lastSyncAt?: true
    createdAt?: true
    updatedAt?: true
  }

  export type LocalUserProfileCountAggregateInputType = {
    id?: true
    userId?: true
    publicId?: true
    email?: true
    name?: true
    hasCompletedOnboarding?: true
    topics?: true
    topicsDetails?: true
    regions?: true
    languages?: true
    publications?: true
    lastSyncAt?: true
    createdAt?: true
    updatedAt?: true
    _all?: true
  }

  export type LocalUserProfileAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which LocalUserProfile to aggregate.
     */
    where?: LocalUserProfileWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalUserProfiles to fetch.
     */
    orderBy?: LocalUserProfileOrderByWithRelationInput | LocalUserProfileOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: LocalUserProfileWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalUserProfiles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalUserProfiles.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned LocalUserProfiles
    **/
    _count?: true | LocalUserProfileCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: LocalUserProfileMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: LocalUserProfileMaxAggregateInputType
  }

  export type GetLocalUserProfileAggregateType<T extends LocalUserProfileAggregateArgs> = {
        [P in keyof T & keyof AggregateLocalUserProfile]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateLocalUserProfile[P]>
      : GetScalarType<T[P], AggregateLocalUserProfile[P]>
  }




  export type LocalUserProfileGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: LocalUserProfileWhereInput
    orderBy?: LocalUserProfileOrderByWithAggregationInput | LocalUserProfileOrderByWithAggregationInput[]
    by: LocalUserProfileScalarFieldEnum[] | LocalUserProfileScalarFieldEnum
    having?: LocalUserProfileScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: LocalUserProfileCountAggregateInputType | true
    _min?: LocalUserProfileMinAggregateInputType
    _max?: LocalUserProfileMaxAggregateInputType
  }

  export type LocalUserProfileGroupByOutputType = {
    id: string
    userId: string
    publicId: string
    email: string
    name: string
    hasCompletedOnboarding: boolean
    topics: string
    topicsDetails: string | null
    regions: string
    languages: string
    publications: string
    lastSyncAt: Date
    createdAt: Date
    updatedAt: Date
    _count: LocalUserProfileCountAggregateOutputType | null
    _min: LocalUserProfileMinAggregateOutputType | null
    _max: LocalUserProfileMaxAggregateOutputType | null
  }

  type GetLocalUserProfileGroupByPayload<T extends LocalUserProfileGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<LocalUserProfileGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof LocalUserProfileGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], LocalUserProfileGroupByOutputType[P]>
            : GetScalarType<T[P], LocalUserProfileGroupByOutputType[P]>
        }
      >
    >


  export type LocalUserProfileSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    publicId?: boolean
    email?: boolean
    name?: boolean
    hasCompletedOnboarding?: boolean
    topics?: boolean
    topicsDetails?: boolean
    regions?: boolean
    languages?: boolean
    publications?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    feedSyncs?: boolean | LocalUserProfile$feedSyncsArgs<ExtArgs>
    _count?: boolean | LocalUserProfileCountOutputTypeDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["localUserProfile"]>

  export type LocalUserProfileSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    publicId?: boolean
    email?: boolean
    name?: boolean
    hasCompletedOnboarding?: boolean
    topics?: boolean
    topicsDetails?: boolean
    regions?: boolean
    languages?: boolean
    publications?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["localUserProfile"]>

  export type LocalUserProfileSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    publicId?: boolean
    email?: boolean
    name?: boolean
    hasCompletedOnboarding?: boolean
    topics?: boolean
    topicsDetails?: boolean
    regions?: boolean
    languages?: boolean
    publications?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["localUserProfile"]>

  export type LocalUserProfileSelectScalar = {
    id?: boolean
    userId?: boolean
    publicId?: boolean
    email?: boolean
    name?: boolean
    hasCompletedOnboarding?: boolean
    topics?: boolean
    topicsDetails?: boolean
    regions?: boolean
    languages?: boolean
    publications?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }

  export type LocalUserProfileOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "userId" | "publicId" | "email" | "name" | "hasCompletedOnboarding" | "topics" | "topicsDetails" | "regions" | "languages" | "publications" | "lastSyncAt" | "createdAt" | "updatedAt", ExtArgs["result"]["localUserProfile"]>
  export type LocalUserProfileInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedSyncs?: boolean | LocalUserProfile$feedSyncsArgs<ExtArgs>
    _count?: boolean | LocalUserProfileCountOutputTypeDefaultArgs<ExtArgs>
  }
  export type LocalUserProfileIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}
  export type LocalUserProfileIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}

  export type $LocalUserProfilePayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "LocalUserProfile"
    objects: {
      feedSyncs: Prisma.$FeedSyncPayload<ExtArgs>[]
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      userId: string
      publicId: string
      email: string
      name: string
      hasCompletedOnboarding: boolean
      topics: string
      topicsDetails: string | null
      regions: string
      languages: string
      publications: string
      lastSyncAt: Date
      createdAt: Date
      updatedAt: Date
    }, ExtArgs["result"]["localUserProfile"]>
    composites: {}
  }

  type LocalUserProfileGetPayload<S extends boolean | null | undefined | LocalUserProfileDefaultArgs> = $Result.GetResult<Prisma.$LocalUserProfilePayload, S>

  type LocalUserProfileCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<LocalUserProfileFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: LocalUserProfileCountAggregateInputType | true
    }

  export interface LocalUserProfileDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['LocalUserProfile'], meta: { name: 'LocalUserProfile' } }
    /**
     * Find zero or one LocalUserProfile that matches the filter.
     * @param {LocalUserProfileFindUniqueArgs} args - Arguments to find a LocalUserProfile
     * @example
     * // Get one LocalUserProfile
     * const localUserProfile = await prisma.localUserProfile.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends LocalUserProfileFindUniqueArgs>(args: SelectSubset<T, LocalUserProfileFindUniqueArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one LocalUserProfile that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {LocalUserProfileFindUniqueOrThrowArgs} args - Arguments to find a LocalUserProfile
     * @example
     * // Get one LocalUserProfile
     * const localUserProfile = await prisma.localUserProfile.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends LocalUserProfileFindUniqueOrThrowArgs>(args: SelectSubset<T, LocalUserProfileFindUniqueOrThrowArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first LocalUserProfile that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileFindFirstArgs} args - Arguments to find a LocalUserProfile
     * @example
     * // Get one LocalUserProfile
     * const localUserProfile = await prisma.localUserProfile.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends LocalUserProfileFindFirstArgs>(args?: SelectSubset<T, LocalUserProfileFindFirstArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first LocalUserProfile that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileFindFirstOrThrowArgs} args - Arguments to find a LocalUserProfile
     * @example
     * // Get one LocalUserProfile
     * const localUserProfile = await prisma.localUserProfile.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends LocalUserProfileFindFirstOrThrowArgs>(args?: SelectSubset<T, LocalUserProfileFindFirstOrThrowArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more LocalUserProfiles that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all LocalUserProfiles
     * const localUserProfiles = await prisma.localUserProfile.findMany()
     * 
     * // Get first 10 LocalUserProfiles
     * const localUserProfiles = await prisma.localUserProfile.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const localUserProfileWithIdOnly = await prisma.localUserProfile.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends LocalUserProfileFindManyArgs>(args?: SelectSubset<T, LocalUserProfileFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a LocalUserProfile.
     * @param {LocalUserProfileCreateArgs} args - Arguments to create a LocalUserProfile.
     * @example
     * // Create one LocalUserProfile
     * const LocalUserProfile = await prisma.localUserProfile.create({
     *   data: {
     *     // ... data to create a LocalUserProfile
     *   }
     * })
     * 
     */
    create<T extends LocalUserProfileCreateArgs>(args: SelectSubset<T, LocalUserProfileCreateArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many LocalUserProfiles.
     * @param {LocalUserProfileCreateManyArgs} args - Arguments to create many LocalUserProfiles.
     * @example
     * // Create many LocalUserProfiles
     * const localUserProfile = await prisma.localUserProfile.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends LocalUserProfileCreateManyArgs>(args?: SelectSubset<T, LocalUserProfileCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many LocalUserProfiles and returns the data saved in the database.
     * @param {LocalUserProfileCreateManyAndReturnArgs} args - Arguments to create many LocalUserProfiles.
     * @example
     * // Create many LocalUserProfiles
     * const localUserProfile = await prisma.localUserProfile.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many LocalUserProfiles and only return the `id`
     * const localUserProfileWithIdOnly = await prisma.localUserProfile.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends LocalUserProfileCreateManyAndReturnArgs>(args?: SelectSubset<T, LocalUserProfileCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a LocalUserProfile.
     * @param {LocalUserProfileDeleteArgs} args - Arguments to delete one LocalUserProfile.
     * @example
     * // Delete one LocalUserProfile
     * const LocalUserProfile = await prisma.localUserProfile.delete({
     *   where: {
     *     // ... filter to delete one LocalUserProfile
     *   }
     * })
     * 
     */
    delete<T extends LocalUserProfileDeleteArgs>(args: SelectSubset<T, LocalUserProfileDeleteArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one LocalUserProfile.
     * @param {LocalUserProfileUpdateArgs} args - Arguments to update one LocalUserProfile.
     * @example
     * // Update one LocalUserProfile
     * const localUserProfile = await prisma.localUserProfile.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends LocalUserProfileUpdateArgs>(args: SelectSubset<T, LocalUserProfileUpdateArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more LocalUserProfiles.
     * @param {LocalUserProfileDeleteManyArgs} args - Arguments to filter LocalUserProfiles to delete.
     * @example
     * // Delete a few LocalUserProfiles
     * const { count } = await prisma.localUserProfile.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends LocalUserProfileDeleteManyArgs>(args?: SelectSubset<T, LocalUserProfileDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more LocalUserProfiles.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many LocalUserProfiles
     * const localUserProfile = await prisma.localUserProfile.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends LocalUserProfileUpdateManyArgs>(args: SelectSubset<T, LocalUserProfileUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more LocalUserProfiles and returns the data updated in the database.
     * @param {LocalUserProfileUpdateManyAndReturnArgs} args - Arguments to update many LocalUserProfiles.
     * @example
     * // Update many LocalUserProfiles
     * const localUserProfile = await prisma.localUserProfile.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more LocalUserProfiles and only return the `id`
     * const localUserProfileWithIdOnly = await prisma.localUserProfile.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends LocalUserProfileUpdateManyAndReturnArgs>(args: SelectSubset<T, LocalUserProfileUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one LocalUserProfile.
     * @param {LocalUserProfileUpsertArgs} args - Arguments to update or create a LocalUserProfile.
     * @example
     * // Update or create a LocalUserProfile
     * const localUserProfile = await prisma.localUserProfile.upsert({
     *   create: {
     *     // ... data to create a LocalUserProfile
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the LocalUserProfile we want to update
     *   }
     * })
     */
    upsert<T extends LocalUserProfileUpsertArgs>(args: SelectSubset<T, LocalUserProfileUpsertArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of LocalUserProfiles.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileCountArgs} args - Arguments to filter LocalUserProfiles to count.
     * @example
     * // Count the number of LocalUserProfiles
     * const count = await prisma.localUserProfile.count({
     *   where: {
     *     // ... the filter for the LocalUserProfiles we want to count
     *   }
     * })
    **/
    count<T extends LocalUserProfileCountArgs>(
      args?: Subset<T, LocalUserProfileCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], LocalUserProfileCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a LocalUserProfile.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends LocalUserProfileAggregateArgs>(args: Subset<T, LocalUserProfileAggregateArgs>): Prisma.PrismaPromise<GetLocalUserProfileAggregateType<T>>

    /**
     * Group by LocalUserProfile.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalUserProfileGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends LocalUserProfileGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: LocalUserProfileGroupByArgs['orderBy'] }
        : { orderBy?: LocalUserProfileGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, LocalUserProfileGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetLocalUserProfileGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the LocalUserProfile model
   */
  readonly fields: LocalUserProfileFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for LocalUserProfile.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__LocalUserProfileClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    feedSyncs<T extends LocalUserProfile$feedSyncsArgs<ExtArgs> = {}>(args?: Subset<T, LocalUserProfile$feedSyncsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the LocalUserProfile model
   */
  interface LocalUserProfileFieldRefs {
    readonly id: FieldRef<"LocalUserProfile", 'String'>
    readonly userId: FieldRef<"LocalUserProfile", 'String'>
    readonly publicId: FieldRef<"LocalUserProfile", 'String'>
    readonly email: FieldRef<"LocalUserProfile", 'String'>
    readonly name: FieldRef<"LocalUserProfile", 'String'>
    readonly hasCompletedOnboarding: FieldRef<"LocalUserProfile", 'Boolean'>
    readonly topics: FieldRef<"LocalUserProfile", 'String'>
    readonly topicsDetails: FieldRef<"LocalUserProfile", 'String'>
    readonly regions: FieldRef<"LocalUserProfile", 'String'>
    readonly languages: FieldRef<"LocalUserProfile", 'String'>
    readonly publications: FieldRef<"LocalUserProfile", 'String'>
    readonly lastSyncAt: FieldRef<"LocalUserProfile", 'DateTime'>
    readonly createdAt: FieldRef<"LocalUserProfile", 'DateTime'>
    readonly updatedAt: FieldRef<"LocalUserProfile", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * LocalUserProfile findUnique
   */
  export type LocalUserProfileFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * Filter, which LocalUserProfile to fetch.
     */
    where: LocalUserProfileWhereUniqueInput
  }

  /**
   * LocalUserProfile findUniqueOrThrow
   */
  export type LocalUserProfileFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * Filter, which LocalUserProfile to fetch.
     */
    where: LocalUserProfileWhereUniqueInput
  }

  /**
   * LocalUserProfile findFirst
   */
  export type LocalUserProfileFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * Filter, which LocalUserProfile to fetch.
     */
    where?: LocalUserProfileWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalUserProfiles to fetch.
     */
    orderBy?: LocalUserProfileOrderByWithRelationInput | LocalUserProfileOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for LocalUserProfiles.
     */
    cursor?: LocalUserProfileWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalUserProfiles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalUserProfiles.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of LocalUserProfiles.
     */
    distinct?: LocalUserProfileScalarFieldEnum | LocalUserProfileScalarFieldEnum[]
  }

  /**
   * LocalUserProfile findFirstOrThrow
   */
  export type LocalUserProfileFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * Filter, which LocalUserProfile to fetch.
     */
    where?: LocalUserProfileWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalUserProfiles to fetch.
     */
    orderBy?: LocalUserProfileOrderByWithRelationInput | LocalUserProfileOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for LocalUserProfiles.
     */
    cursor?: LocalUserProfileWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalUserProfiles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalUserProfiles.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of LocalUserProfiles.
     */
    distinct?: LocalUserProfileScalarFieldEnum | LocalUserProfileScalarFieldEnum[]
  }

  /**
   * LocalUserProfile findMany
   */
  export type LocalUserProfileFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * Filter, which LocalUserProfiles to fetch.
     */
    where?: LocalUserProfileWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalUserProfiles to fetch.
     */
    orderBy?: LocalUserProfileOrderByWithRelationInput | LocalUserProfileOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing LocalUserProfiles.
     */
    cursor?: LocalUserProfileWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalUserProfiles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalUserProfiles.
     */
    skip?: number
    distinct?: LocalUserProfileScalarFieldEnum | LocalUserProfileScalarFieldEnum[]
  }

  /**
   * LocalUserProfile create
   */
  export type LocalUserProfileCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * The data needed to create a LocalUserProfile.
     */
    data: XOR<LocalUserProfileCreateInput, LocalUserProfileUncheckedCreateInput>
  }

  /**
   * LocalUserProfile createMany
   */
  export type LocalUserProfileCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many LocalUserProfiles.
     */
    data: LocalUserProfileCreateManyInput | LocalUserProfileCreateManyInput[]
  }

  /**
   * LocalUserProfile createManyAndReturn
   */
  export type LocalUserProfileCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * The data used to create many LocalUserProfiles.
     */
    data: LocalUserProfileCreateManyInput | LocalUserProfileCreateManyInput[]
  }

  /**
   * LocalUserProfile update
   */
  export type LocalUserProfileUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * The data needed to update a LocalUserProfile.
     */
    data: XOR<LocalUserProfileUpdateInput, LocalUserProfileUncheckedUpdateInput>
    /**
     * Choose, which LocalUserProfile to update.
     */
    where: LocalUserProfileWhereUniqueInput
  }

  /**
   * LocalUserProfile updateMany
   */
  export type LocalUserProfileUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update LocalUserProfiles.
     */
    data: XOR<LocalUserProfileUpdateManyMutationInput, LocalUserProfileUncheckedUpdateManyInput>
    /**
     * Filter which LocalUserProfiles to update
     */
    where?: LocalUserProfileWhereInput
    /**
     * Limit how many LocalUserProfiles to update.
     */
    limit?: number
  }

  /**
   * LocalUserProfile updateManyAndReturn
   */
  export type LocalUserProfileUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * The data used to update LocalUserProfiles.
     */
    data: XOR<LocalUserProfileUpdateManyMutationInput, LocalUserProfileUncheckedUpdateManyInput>
    /**
     * Filter which LocalUserProfiles to update
     */
    where?: LocalUserProfileWhereInput
    /**
     * Limit how many LocalUserProfiles to update.
     */
    limit?: number
  }

  /**
   * LocalUserProfile upsert
   */
  export type LocalUserProfileUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * The filter to search for the LocalUserProfile to update in case it exists.
     */
    where: LocalUserProfileWhereUniqueInput
    /**
     * In case the LocalUserProfile found by the `where` argument doesn't exist, create a new LocalUserProfile with this data.
     */
    create: XOR<LocalUserProfileCreateInput, LocalUserProfileUncheckedCreateInput>
    /**
     * In case the LocalUserProfile was found with the provided `where` argument, update it with this data.
     */
    update: XOR<LocalUserProfileUpdateInput, LocalUserProfileUncheckedUpdateInput>
  }

  /**
   * LocalUserProfile delete
   */
  export type LocalUserProfileDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
    /**
     * Filter which LocalUserProfile to delete.
     */
    where: LocalUserProfileWhereUniqueInput
  }

  /**
   * LocalUserProfile deleteMany
   */
  export type LocalUserProfileDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which LocalUserProfiles to delete
     */
    where?: LocalUserProfileWhereInput
    /**
     * Limit how many LocalUserProfiles to delete.
     */
    limit?: number
  }

  /**
   * LocalUserProfile.feedSyncs
   */
  export type LocalUserProfile$feedSyncsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    where?: FeedSyncWhereInput
    orderBy?: FeedSyncOrderByWithRelationInput | FeedSyncOrderByWithRelationInput[]
    cursor?: FeedSyncWhereUniqueInput
    take?: number
    skip?: number
    distinct?: FeedSyncScalarFieldEnum | FeedSyncScalarFieldEnum[]
  }

  /**
   * LocalUserProfile without action
   */
  export type LocalUserProfileDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalUserProfile
     */
    select?: LocalUserProfileSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalUserProfile
     */
    omit?: LocalUserProfileOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalUserProfileInclude<ExtArgs> | null
  }


  /**
   * Model LocalArticle
   */

  export type AggregateLocalArticle = {
    _count: LocalArticleCountAggregateOutputType | null
    _avg: LocalArticleAvgAggregateOutputType | null
    _sum: LocalArticleSumAggregateOutputType | null
    _min: LocalArticleMinAggregateOutputType | null
    _max: LocalArticleMaxAggregateOutputType | null
  }

  export type LocalArticleAvgAggregateOutputType = {
    readTime: number | null
  }

  export type LocalArticleSumAggregateOutputType = {
    readTime: number | null
  }

  export type LocalArticleMinAggregateOutputType = {
    id: string | null
    backendId: string | null
    title: string | null
    visualTitle: string | null
    description: string | null
    content: string | null
    url: string | null
    imageUrl: string | null
    publishedAt: Date | null
    readTime: number | null
    isTopHeadline: boolean | null
    sourceName: string | null
    sourceLogoUrl: string | null
    summary: string | null
    richContent: string | null
    contentStatus: string | null
    contentQuality: string | null
    topics: string | null
    isRead: boolean | null
    isSaved: boolean | null
    readAt: Date | null
    savedAt: Date | null
    lastSyncAt: Date | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type LocalArticleMaxAggregateOutputType = {
    id: string | null
    backendId: string | null
    title: string | null
    visualTitle: string | null
    description: string | null
    content: string | null
    url: string | null
    imageUrl: string | null
    publishedAt: Date | null
    readTime: number | null
    isTopHeadline: boolean | null
    sourceName: string | null
    sourceLogoUrl: string | null
    summary: string | null
    richContent: string | null
    contentStatus: string | null
    contentQuality: string | null
    topics: string | null
    isRead: boolean | null
    isSaved: boolean | null
    readAt: Date | null
    savedAt: Date | null
    lastSyncAt: Date | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type LocalArticleCountAggregateOutputType = {
    id: number
    backendId: number
    title: number
    visualTitle: number
    description: number
    content: number
    url: number
    imageUrl: number
    publishedAt: number
    readTime: number
    isTopHeadline: number
    sourceName: number
    sourceLogoUrl: number
    summary: number
    richContent: number
    contentStatus: number
    contentQuality: number
    topics: number
    isRead: number
    isSaved: number
    readAt: number
    savedAt: number
    lastSyncAt: number
    createdAt: number
    updatedAt: number
    _all: number
  }


  export type LocalArticleAvgAggregateInputType = {
    readTime?: true
  }

  export type LocalArticleSumAggregateInputType = {
    readTime?: true
  }

  export type LocalArticleMinAggregateInputType = {
    id?: true
    backendId?: true
    title?: true
    visualTitle?: true
    description?: true
    content?: true
    url?: true
    imageUrl?: true
    publishedAt?: true
    readTime?: true
    isTopHeadline?: true
    sourceName?: true
    sourceLogoUrl?: true
    summary?: true
    richContent?: true
    contentStatus?: true
    contentQuality?: true
    topics?: true
    isRead?: true
    isSaved?: true
    readAt?: true
    savedAt?: true
    lastSyncAt?: true
    createdAt?: true
    updatedAt?: true
  }

  export type LocalArticleMaxAggregateInputType = {
    id?: true
    backendId?: true
    title?: true
    visualTitle?: true
    description?: true
    content?: true
    url?: true
    imageUrl?: true
    publishedAt?: true
    readTime?: true
    isTopHeadline?: true
    sourceName?: true
    sourceLogoUrl?: true
    summary?: true
    richContent?: true
    contentStatus?: true
    contentQuality?: true
    topics?: true
    isRead?: true
    isSaved?: true
    readAt?: true
    savedAt?: true
    lastSyncAt?: true
    createdAt?: true
    updatedAt?: true
  }

  export type LocalArticleCountAggregateInputType = {
    id?: true
    backendId?: true
    title?: true
    visualTitle?: true
    description?: true
    content?: true
    url?: true
    imageUrl?: true
    publishedAt?: true
    readTime?: true
    isTopHeadline?: true
    sourceName?: true
    sourceLogoUrl?: true
    summary?: true
    richContent?: true
    contentStatus?: true
    contentQuality?: true
    topics?: true
    isRead?: true
    isSaved?: true
    readAt?: true
    savedAt?: true
    lastSyncAt?: true
    createdAt?: true
    updatedAt?: true
    _all?: true
  }

  export type LocalArticleAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which LocalArticle to aggregate.
     */
    where?: LocalArticleWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalArticles to fetch.
     */
    orderBy?: LocalArticleOrderByWithRelationInput | LocalArticleOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: LocalArticleWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalArticles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalArticles.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned LocalArticles
    **/
    _count?: true | LocalArticleCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: LocalArticleAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: LocalArticleSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: LocalArticleMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: LocalArticleMaxAggregateInputType
  }

  export type GetLocalArticleAggregateType<T extends LocalArticleAggregateArgs> = {
        [P in keyof T & keyof AggregateLocalArticle]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateLocalArticle[P]>
      : GetScalarType<T[P], AggregateLocalArticle[P]>
  }




  export type LocalArticleGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: LocalArticleWhereInput
    orderBy?: LocalArticleOrderByWithAggregationInput | LocalArticleOrderByWithAggregationInput[]
    by: LocalArticleScalarFieldEnum[] | LocalArticleScalarFieldEnum
    having?: LocalArticleScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: LocalArticleCountAggregateInputType | true
    _avg?: LocalArticleAvgAggregateInputType
    _sum?: LocalArticleSumAggregateInputType
    _min?: LocalArticleMinAggregateInputType
    _max?: LocalArticleMaxAggregateInputType
  }

  export type LocalArticleGroupByOutputType = {
    id: string
    backendId: string
    title: string
    visualTitle: string | null
    description: string
    content: string | null
    url: string
    imageUrl: string | null
    publishedAt: Date
    readTime: number | null
    isTopHeadline: boolean
    sourceName: string
    sourceLogoUrl: string | null
    summary: string | null
    richContent: string | null
    contentStatus: string | null
    contentQuality: string | null
    topics: string | null
    isRead: boolean
    isSaved: boolean
    readAt: Date | null
    savedAt: Date | null
    lastSyncAt: Date
    createdAt: Date
    updatedAt: Date
    _count: LocalArticleCountAggregateOutputType | null
    _avg: LocalArticleAvgAggregateOutputType | null
    _sum: LocalArticleSumAggregateOutputType | null
    _min: LocalArticleMinAggregateOutputType | null
    _max: LocalArticleMaxAggregateOutputType | null
  }

  type GetLocalArticleGroupByPayload<T extends LocalArticleGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<LocalArticleGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof LocalArticleGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], LocalArticleGroupByOutputType[P]>
            : GetScalarType<T[P], LocalArticleGroupByOutputType[P]>
        }
      >
    >


  export type LocalArticleSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    backendId?: boolean
    title?: boolean
    visualTitle?: boolean
    description?: boolean
    content?: boolean
    url?: boolean
    imageUrl?: boolean
    publishedAt?: boolean
    readTime?: boolean
    isTopHeadline?: boolean
    sourceName?: boolean
    sourceLogoUrl?: boolean
    summary?: boolean
    richContent?: boolean
    contentStatus?: boolean
    contentQuality?: boolean
    topics?: boolean
    isRead?: boolean
    isSaved?: boolean
    readAt?: boolean
    savedAt?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    feedItems?: boolean | LocalArticle$feedItemsArgs<ExtArgs>
    _count?: boolean | LocalArticleCountOutputTypeDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["localArticle"]>

  export type LocalArticleSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    backendId?: boolean
    title?: boolean
    visualTitle?: boolean
    description?: boolean
    content?: boolean
    url?: boolean
    imageUrl?: boolean
    publishedAt?: boolean
    readTime?: boolean
    isTopHeadline?: boolean
    sourceName?: boolean
    sourceLogoUrl?: boolean
    summary?: boolean
    richContent?: boolean
    contentStatus?: boolean
    contentQuality?: boolean
    topics?: boolean
    isRead?: boolean
    isSaved?: boolean
    readAt?: boolean
    savedAt?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["localArticle"]>

  export type LocalArticleSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    backendId?: boolean
    title?: boolean
    visualTitle?: boolean
    description?: boolean
    content?: boolean
    url?: boolean
    imageUrl?: boolean
    publishedAt?: boolean
    readTime?: boolean
    isTopHeadline?: boolean
    sourceName?: boolean
    sourceLogoUrl?: boolean
    summary?: boolean
    richContent?: boolean
    contentStatus?: boolean
    contentQuality?: boolean
    topics?: boolean
    isRead?: boolean
    isSaved?: boolean
    readAt?: boolean
    savedAt?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["localArticle"]>

  export type LocalArticleSelectScalar = {
    id?: boolean
    backendId?: boolean
    title?: boolean
    visualTitle?: boolean
    description?: boolean
    content?: boolean
    url?: boolean
    imageUrl?: boolean
    publishedAt?: boolean
    readTime?: boolean
    isTopHeadline?: boolean
    sourceName?: boolean
    sourceLogoUrl?: boolean
    summary?: boolean
    richContent?: boolean
    contentStatus?: boolean
    contentQuality?: boolean
    topics?: boolean
    isRead?: boolean
    isSaved?: boolean
    readAt?: boolean
    savedAt?: boolean
    lastSyncAt?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }

  export type LocalArticleOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "backendId" | "title" | "visualTitle" | "description" | "content" | "url" | "imageUrl" | "publishedAt" | "readTime" | "isTopHeadline" | "sourceName" | "sourceLogoUrl" | "summary" | "richContent" | "contentStatus" | "contentQuality" | "topics" | "isRead" | "isSaved" | "readAt" | "savedAt" | "lastSyncAt" | "createdAt" | "updatedAt", ExtArgs["result"]["localArticle"]>
  export type LocalArticleInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedItems?: boolean | LocalArticle$feedItemsArgs<ExtArgs>
    _count?: boolean | LocalArticleCountOutputTypeDefaultArgs<ExtArgs>
  }
  export type LocalArticleIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}
  export type LocalArticleIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {}

  export type $LocalArticlePayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "LocalArticle"
    objects: {
      feedItems: Prisma.$FeedItemPayload<ExtArgs>[]
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      backendId: string
      title: string
      visualTitle: string | null
      description: string
      content: string | null
      url: string
      imageUrl: string | null
      publishedAt: Date
      readTime: number | null
      isTopHeadline: boolean
      sourceName: string
      sourceLogoUrl: string | null
      summary: string | null
      richContent: string | null
      contentStatus: string | null
      contentQuality: string | null
      topics: string | null
      isRead: boolean
      isSaved: boolean
      readAt: Date | null
      savedAt: Date | null
      lastSyncAt: Date
      createdAt: Date
      updatedAt: Date
    }, ExtArgs["result"]["localArticle"]>
    composites: {}
  }

  type LocalArticleGetPayload<S extends boolean | null | undefined | LocalArticleDefaultArgs> = $Result.GetResult<Prisma.$LocalArticlePayload, S>

  type LocalArticleCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<LocalArticleFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: LocalArticleCountAggregateInputType | true
    }

  export interface LocalArticleDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['LocalArticle'], meta: { name: 'LocalArticle' } }
    /**
     * Find zero or one LocalArticle that matches the filter.
     * @param {LocalArticleFindUniqueArgs} args - Arguments to find a LocalArticle
     * @example
     * // Get one LocalArticle
     * const localArticle = await prisma.localArticle.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends LocalArticleFindUniqueArgs>(args: SelectSubset<T, LocalArticleFindUniqueArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one LocalArticle that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {LocalArticleFindUniqueOrThrowArgs} args - Arguments to find a LocalArticle
     * @example
     * // Get one LocalArticle
     * const localArticle = await prisma.localArticle.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends LocalArticleFindUniqueOrThrowArgs>(args: SelectSubset<T, LocalArticleFindUniqueOrThrowArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first LocalArticle that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleFindFirstArgs} args - Arguments to find a LocalArticle
     * @example
     * // Get one LocalArticle
     * const localArticle = await prisma.localArticle.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends LocalArticleFindFirstArgs>(args?: SelectSubset<T, LocalArticleFindFirstArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first LocalArticle that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleFindFirstOrThrowArgs} args - Arguments to find a LocalArticle
     * @example
     * // Get one LocalArticle
     * const localArticle = await prisma.localArticle.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends LocalArticleFindFirstOrThrowArgs>(args?: SelectSubset<T, LocalArticleFindFirstOrThrowArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more LocalArticles that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all LocalArticles
     * const localArticles = await prisma.localArticle.findMany()
     * 
     * // Get first 10 LocalArticles
     * const localArticles = await prisma.localArticle.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const localArticleWithIdOnly = await prisma.localArticle.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends LocalArticleFindManyArgs>(args?: SelectSubset<T, LocalArticleFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a LocalArticle.
     * @param {LocalArticleCreateArgs} args - Arguments to create a LocalArticle.
     * @example
     * // Create one LocalArticle
     * const LocalArticle = await prisma.localArticle.create({
     *   data: {
     *     // ... data to create a LocalArticle
     *   }
     * })
     * 
     */
    create<T extends LocalArticleCreateArgs>(args: SelectSubset<T, LocalArticleCreateArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many LocalArticles.
     * @param {LocalArticleCreateManyArgs} args - Arguments to create many LocalArticles.
     * @example
     * // Create many LocalArticles
     * const localArticle = await prisma.localArticle.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends LocalArticleCreateManyArgs>(args?: SelectSubset<T, LocalArticleCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many LocalArticles and returns the data saved in the database.
     * @param {LocalArticleCreateManyAndReturnArgs} args - Arguments to create many LocalArticles.
     * @example
     * // Create many LocalArticles
     * const localArticle = await prisma.localArticle.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many LocalArticles and only return the `id`
     * const localArticleWithIdOnly = await prisma.localArticle.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends LocalArticleCreateManyAndReturnArgs>(args?: SelectSubset<T, LocalArticleCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a LocalArticle.
     * @param {LocalArticleDeleteArgs} args - Arguments to delete one LocalArticle.
     * @example
     * // Delete one LocalArticle
     * const LocalArticle = await prisma.localArticle.delete({
     *   where: {
     *     // ... filter to delete one LocalArticle
     *   }
     * })
     * 
     */
    delete<T extends LocalArticleDeleteArgs>(args: SelectSubset<T, LocalArticleDeleteArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one LocalArticle.
     * @param {LocalArticleUpdateArgs} args - Arguments to update one LocalArticle.
     * @example
     * // Update one LocalArticle
     * const localArticle = await prisma.localArticle.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends LocalArticleUpdateArgs>(args: SelectSubset<T, LocalArticleUpdateArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more LocalArticles.
     * @param {LocalArticleDeleteManyArgs} args - Arguments to filter LocalArticles to delete.
     * @example
     * // Delete a few LocalArticles
     * const { count } = await prisma.localArticle.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends LocalArticleDeleteManyArgs>(args?: SelectSubset<T, LocalArticleDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more LocalArticles.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many LocalArticles
     * const localArticle = await prisma.localArticle.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends LocalArticleUpdateManyArgs>(args: SelectSubset<T, LocalArticleUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more LocalArticles and returns the data updated in the database.
     * @param {LocalArticleUpdateManyAndReturnArgs} args - Arguments to update many LocalArticles.
     * @example
     * // Update many LocalArticles
     * const localArticle = await prisma.localArticle.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more LocalArticles and only return the `id`
     * const localArticleWithIdOnly = await prisma.localArticle.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends LocalArticleUpdateManyAndReturnArgs>(args: SelectSubset<T, LocalArticleUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one LocalArticle.
     * @param {LocalArticleUpsertArgs} args - Arguments to update or create a LocalArticle.
     * @example
     * // Update or create a LocalArticle
     * const localArticle = await prisma.localArticle.upsert({
     *   create: {
     *     // ... data to create a LocalArticle
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the LocalArticle we want to update
     *   }
     * })
     */
    upsert<T extends LocalArticleUpsertArgs>(args: SelectSubset<T, LocalArticleUpsertArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of LocalArticles.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleCountArgs} args - Arguments to filter LocalArticles to count.
     * @example
     * // Count the number of LocalArticles
     * const count = await prisma.localArticle.count({
     *   where: {
     *     // ... the filter for the LocalArticles we want to count
     *   }
     * })
    **/
    count<T extends LocalArticleCountArgs>(
      args?: Subset<T, LocalArticleCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], LocalArticleCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a LocalArticle.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends LocalArticleAggregateArgs>(args: Subset<T, LocalArticleAggregateArgs>): Prisma.PrismaPromise<GetLocalArticleAggregateType<T>>

    /**
     * Group by LocalArticle.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {LocalArticleGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends LocalArticleGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: LocalArticleGroupByArgs['orderBy'] }
        : { orderBy?: LocalArticleGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, LocalArticleGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetLocalArticleGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the LocalArticle model
   */
  readonly fields: LocalArticleFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for LocalArticle.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__LocalArticleClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    feedItems<T extends LocalArticle$feedItemsArgs<ExtArgs> = {}>(args?: Subset<T, LocalArticle$feedItemsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the LocalArticle model
   */
  interface LocalArticleFieldRefs {
    readonly id: FieldRef<"LocalArticle", 'String'>
    readonly backendId: FieldRef<"LocalArticle", 'String'>
    readonly title: FieldRef<"LocalArticle", 'String'>
    readonly visualTitle: FieldRef<"LocalArticle", 'String'>
    readonly description: FieldRef<"LocalArticle", 'String'>
    readonly content: FieldRef<"LocalArticle", 'String'>
    readonly url: FieldRef<"LocalArticle", 'String'>
    readonly imageUrl: FieldRef<"LocalArticle", 'String'>
    readonly publishedAt: FieldRef<"LocalArticle", 'DateTime'>
    readonly readTime: FieldRef<"LocalArticle", 'Int'>
    readonly isTopHeadline: FieldRef<"LocalArticle", 'Boolean'>
    readonly sourceName: FieldRef<"LocalArticle", 'String'>
    readonly sourceLogoUrl: FieldRef<"LocalArticle", 'String'>
    readonly summary: FieldRef<"LocalArticle", 'String'>
    readonly richContent: FieldRef<"LocalArticle", 'String'>
    readonly contentStatus: FieldRef<"LocalArticle", 'String'>
    readonly contentQuality: FieldRef<"LocalArticle", 'String'>
    readonly topics: FieldRef<"LocalArticle", 'String'>
    readonly isRead: FieldRef<"LocalArticle", 'Boolean'>
    readonly isSaved: FieldRef<"LocalArticle", 'Boolean'>
    readonly readAt: FieldRef<"LocalArticle", 'DateTime'>
    readonly savedAt: FieldRef<"LocalArticle", 'DateTime'>
    readonly lastSyncAt: FieldRef<"LocalArticle", 'DateTime'>
    readonly createdAt: FieldRef<"LocalArticle", 'DateTime'>
    readonly updatedAt: FieldRef<"LocalArticle", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * LocalArticle findUnique
   */
  export type LocalArticleFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * Filter, which LocalArticle to fetch.
     */
    where: LocalArticleWhereUniqueInput
  }

  /**
   * LocalArticle findUniqueOrThrow
   */
  export type LocalArticleFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * Filter, which LocalArticle to fetch.
     */
    where: LocalArticleWhereUniqueInput
  }

  /**
   * LocalArticle findFirst
   */
  export type LocalArticleFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * Filter, which LocalArticle to fetch.
     */
    where?: LocalArticleWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalArticles to fetch.
     */
    orderBy?: LocalArticleOrderByWithRelationInput | LocalArticleOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for LocalArticles.
     */
    cursor?: LocalArticleWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalArticles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalArticles.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of LocalArticles.
     */
    distinct?: LocalArticleScalarFieldEnum | LocalArticleScalarFieldEnum[]
  }

  /**
   * LocalArticle findFirstOrThrow
   */
  export type LocalArticleFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * Filter, which LocalArticle to fetch.
     */
    where?: LocalArticleWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalArticles to fetch.
     */
    orderBy?: LocalArticleOrderByWithRelationInput | LocalArticleOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for LocalArticles.
     */
    cursor?: LocalArticleWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalArticles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalArticles.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of LocalArticles.
     */
    distinct?: LocalArticleScalarFieldEnum | LocalArticleScalarFieldEnum[]
  }

  /**
   * LocalArticle findMany
   */
  export type LocalArticleFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * Filter, which LocalArticles to fetch.
     */
    where?: LocalArticleWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of LocalArticles to fetch.
     */
    orderBy?: LocalArticleOrderByWithRelationInput | LocalArticleOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing LocalArticles.
     */
    cursor?: LocalArticleWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` LocalArticles from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` LocalArticles.
     */
    skip?: number
    distinct?: LocalArticleScalarFieldEnum | LocalArticleScalarFieldEnum[]
  }

  /**
   * LocalArticle create
   */
  export type LocalArticleCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * The data needed to create a LocalArticle.
     */
    data: XOR<LocalArticleCreateInput, LocalArticleUncheckedCreateInput>
  }

  /**
   * LocalArticle createMany
   */
  export type LocalArticleCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many LocalArticles.
     */
    data: LocalArticleCreateManyInput | LocalArticleCreateManyInput[]
  }

  /**
   * LocalArticle createManyAndReturn
   */
  export type LocalArticleCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * The data used to create many LocalArticles.
     */
    data: LocalArticleCreateManyInput | LocalArticleCreateManyInput[]
  }

  /**
   * LocalArticle update
   */
  export type LocalArticleUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * The data needed to update a LocalArticle.
     */
    data: XOR<LocalArticleUpdateInput, LocalArticleUncheckedUpdateInput>
    /**
     * Choose, which LocalArticle to update.
     */
    where: LocalArticleWhereUniqueInput
  }

  /**
   * LocalArticle updateMany
   */
  export type LocalArticleUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update LocalArticles.
     */
    data: XOR<LocalArticleUpdateManyMutationInput, LocalArticleUncheckedUpdateManyInput>
    /**
     * Filter which LocalArticles to update
     */
    where?: LocalArticleWhereInput
    /**
     * Limit how many LocalArticles to update.
     */
    limit?: number
  }

  /**
   * LocalArticle updateManyAndReturn
   */
  export type LocalArticleUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * The data used to update LocalArticles.
     */
    data: XOR<LocalArticleUpdateManyMutationInput, LocalArticleUncheckedUpdateManyInput>
    /**
     * Filter which LocalArticles to update
     */
    where?: LocalArticleWhereInput
    /**
     * Limit how many LocalArticles to update.
     */
    limit?: number
  }

  /**
   * LocalArticle upsert
   */
  export type LocalArticleUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * The filter to search for the LocalArticle to update in case it exists.
     */
    where: LocalArticleWhereUniqueInput
    /**
     * In case the LocalArticle found by the `where` argument doesn't exist, create a new LocalArticle with this data.
     */
    create: XOR<LocalArticleCreateInput, LocalArticleUncheckedCreateInput>
    /**
     * In case the LocalArticle was found with the provided `where` argument, update it with this data.
     */
    update: XOR<LocalArticleUpdateInput, LocalArticleUncheckedUpdateInput>
  }

  /**
   * LocalArticle delete
   */
  export type LocalArticleDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
    /**
     * Filter which LocalArticle to delete.
     */
    where: LocalArticleWhereUniqueInput
  }

  /**
   * LocalArticle deleteMany
   */
  export type LocalArticleDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which LocalArticles to delete
     */
    where?: LocalArticleWhereInput
    /**
     * Limit how many LocalArticles to delete.
     */
    limit?: number
  }

  /**
   * LocalArticle.feedItems
   */
  export type LocalArticle$feedItemsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    where?: FeedItemWhereInput
    orderBy?: FeedItemOrderByWithRelationInput | FeedItemOrderByWithRelationInput[]
    cursor?: FeedItemWhereUniqueInput
    take?: number
    skip?: number
    distinct?: FeedItemScalarFieldEnum | FeedItemScalarFieldEnum[]
  }

  /**
   * LocalArticle without action
   */
  export type LocalArticleDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the LocalArticle
     */
    select?: LocalArticleSelect<ExtArgs> | null
    /**
     * Omit specific fields from the LocalArticle
     */
    omit?: LocalArticleOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: LocalArticleInclude<ExtArgs> | null
  }


  /**
   * Model FeedSync
   */

  export type AggregateFeedSync = {
    _count: FeedSyncCountAggregateOutputType | null
    _avg: FeedSyncAvgAggregateOutputType | null
    _sum: FeedSyncSumAggregateOutputType | null
    _min: FeedSyncMinAggregateOutputType | null
    _max: FeedSyncMaxAggregateOutputType | null
  }

  export type FeedSyncAvgAggregateOutputType = {
    lastPage: number | null
    totalItems: number | null
    syncCount: number | null
    lastSyncDuration: number | null
    consecutiveErrors: number | null
  }

  export type FeedSyncSumAggregateOutputType = {
    lastPage: number | null
    totalItems: number | null
    syncCount: number | null
    lastSyncDuration: number | null
    consecutiveErrors: number | null
  }

  export type FeedSyncMinAggregateOutputType = {
    id: string | null
    userId: string | null
    feedType: string | null
    topicSlug: string | null
    lastSyncAt: Date | null
    nextSyncAt: Date | null
    isStale: boolean | null
    syncInProgress: boolean | null
    lastPage: number | null
    hasMore: boolean | null
    totalItems: number | null
    syncCount: number | null
    lastSyncDuration: number | null
    lastError: string | null
    consecutiveErrors: number | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type FeedSyncMaxAggregateOutputType = {
    id: string | null
    userId: string | null
    feedType: string | null
    topicSlug: string | null
    lastSyncAt: Date | null
    nextSyncAt: Date | null
    isStale: boolean | null
    syncInProgress: boolean | null
    lastPage: number | null
    hasMore: boolean | null
    totalItems: number | null
    syncCount: number | null
    lastSyncDuration: number | null
    lastError: string | null
    consecutiveErrors: number | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type FeedSyncCountAggregateOutputType = {
    id: number
    userId: number
    feedType: number
    topicSlug: number
    lastSyncAt: number
    nextSyncAt: number
    isStale: number
    syncInProgress: number
    lastPage: number
    hasMore: number
    totalItems: number
    syncCount: number
    lastSyncDuration: number
    lastError: number
    consecutiveErrors: number
    createdAt: number
    updatedAt: number
    _all: number
  }


  export type FeedSyncAvgAggregateInputType = {
    lastPage?: true
    totalItems?: true
    syncCount?: true
    lastSyncDuration?: true
    consecutiveErrors?: true
  }

  export type FeedSyncSumAggregateInputType = {
    lastPage?: true
    totalItems?: true
    syncCount?: true
    lastSyncDuration?: true
    consecutiveErrors?: true
  }

  export type FeedSyncMinAggregateInputType = {
    id?: true
    userId?: true
    feedType?: true
    topicSlug?: true
    lastSyncAt?: true
    nextSyncAt?: true
    isStale?: true
    syncInProgress?: true
    lastPage?: true
    hasMore?: true
    totalItems?: true
    syncCount?: true
    lastSyncDuration?: true
    lastError?: true
    consecutiveErrors?: true
    createdAt?: true
    updatedAt?: true
  }

  export type FeedSyncMaxAggregateInputType = {
    id?: true
    userId?: true
    feedType?: true
    topicSlug?: true
    lastSyncAt?: true
    nextSyncAt?: true
    isStale?: true
    syncInProgress?: true
    lastPage?: true
    hasMore?: true
    totalItems?: true
    syncCount?: true
    lastSyncDuration?: true
    lastError?: true
    consecutiveErrors?: true
    createdAt?: true
    updatedAt?: true
  }

  export type FeedSyncCountAggregateInputType = {
    id?: true
    userId?: true
    feedType?: true
    topicSlug?: true
    lastSyncAt?: true
    nextSyncAt?: true
    isStale?: true
    syncInProgress?: true
    lastPage?: true
    hasMore?: true
    totalItems?: true
    syncCount?: true
    lastSyncDuration?: true
    lastError?: true
    consecutiveErrors?: true
    createdAt?: true
    updatedAt?: true
    _all?: true
  }

  export type FeedSyncAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which FeedSync to aggregate.
     */
    where?: FeedSyncWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedSyncs to fetch.
     */
    orderBy?: FeedSyncOrderByWithRelationInput | FeedSyncOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: FeedSyncWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedSyncs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedSyncs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned FeedSyncs
    **/
    _count?: true | FeedSyncCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: FeedSyncAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: FeedSyncSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: FeedSyncMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: FeedSyncMaxAggregateInputType
  }

  export type GetFeedSyncAggregateType<T extends FeedSyncAggregateArgs> = {
        [P in keyof T & keyof AggregateFeedSync]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateFeedSync[P]>
      : GetScalarType<T[P], AggregateFeedSync[P]>
  }




  export type FeedSyncGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FeedSyncWhereInput
    orderBy?: FeedSyncOrderByWithAggregationInput | FeedSyncOrderByWithAggregationInput[]
    by: FeedSyncScalarFieldEnum[] | FeedSyncScalarFieldEnum
    having?: FeedSyncScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: FeedSyncCountAggregateInputType | true
    _avg?: FeedSyncAvgAggregateInputType
    _sum?: FeedSyncSumAggregateInputType
    _min?: FeedSyncMinAggregateInputType
    _max?: FeedSyncMaxAggregateInputType
  }

  export type FeedSyncGroupByOutputType = {
    id: string
    userId: string
    feedType: string
    topicSlug: string | null
    lastSyncAt: Date
    nextSyncAt: Date | null
    isStale: boolean
    syncInProgress: boolean
    lastPage: number
    hasMore: boolean
    totalItems: number | null
    syncCount: number
    lastSyncDuration: number | null
    lastError: string | null
    consecutiveErrors: number
    createdAt: Date
    updatedAt: Date
    _count: FeedSyncCountAggregateOutputType | null
    _avg: FeedSyncAvgAggregateOutputType | null
    _sum: FeedSyncSumAggregateOutputType | null
    _min: FeedSyncMinAggregateOutputType | null
    _max: FeedSyncMaxAggregateOutputType | null
  }

  type GetFeedSyncGroupByPayload<T extends FeedSyncGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<FeedSyncGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof FeedSyncGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], FeedSyncGroupByOutputType[P]>
            : GetScalarType<T[P], FeedSyncGroupByOutputType[P]>
        }
      >
    >


  export type FeedSyncSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    lastSyncAt?: boolean
    nextSyncAt?: boolean
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: boolean
    hasMore?: boolean
    totalItems?: boolean
    syncCount?: boolean
    lastSyncDuration?: boolean
    lastError?: boolean
    consecutiveErrors?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    userProfile?: boolean | LocalUserProfileDefaultArgs<ExtArgs>
    feedItems?: boolean | FeedSync$feedItemsArgs<ExtArgs>
    _count?: boolean | FeedSyncCountOutputTypeDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["feedSync"]>

  export type FeedSyncSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    lastSyncAt?: boolean
    nextSyncAt?: boolean
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: boolean
    hasMore?: boolean
    totalItems?: boolean
    syncCount?: boolean
    lastSyncDuration?: boolean
    lastError?: boolean
    consecutiveErrors?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    userProfile?: boolean | LocalUserProfileDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["feedSync"]>

  export type FeedSyncSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    lastSyncAt?: boolean
    nextSyncAt?: boolean
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: boolean
    hasMore?: boolean
    totalItems?: boolean
    syncCount?: boolean
    lastSyncDuration?: boolean
    lastError?: boolean
    consecutiveErrors?: boolean
    createdAt?: boolean
    updatedAt?: boolean
    userProfile?: boolean | LocalUserProfileDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["feedSync"]>

  export type FeedSyncSelectScalar = {
    id?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    lastSyncAt?: boolean
    nextSyncAt?: boolean
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: boolean
    hasMore?: boolean
    totalItems?: boolean
    syncCount?: boolean
    lastSyncDuration?: boolean
    lastError?: boolean
    consecutiveErrors?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }

  export type FeedSyncOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "userId" | "feedType" | "topicSlug" | "lastSyncAt" | "nextSyncAt" | "isStale" | "syncInProgress" | "lastPage" | "hasMore" | "totalItems" | "syncCount" | "lastSyncDuration" | "lastError" | "consecutiveErrors" | "createdAt" | "updatedAt", ExtArgs["result"]["feedSync"]>
  export type FeedSyncInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    userProfile?: boolean | LocalUserProfileDefaultArgs<ExtArgs>
    feedItems?: boolean | FeedSync$feedItemsArgs<ExtArgs>
    _count?: boolean | FeedSyncCountOutputTypeDefaultArgs<ExtArgs>
  }
  export type FeedSyncIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    userProfile?: boolean | LocalUserProfileDefaultArgs<ExtArgs>
  }
  export type FeedSyncIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    userProfile?: boolean | LocalUserProfileDefaultArgs<ExtArgs>
  }

  export type $FeedSyncPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "FeedSync"
    objects: {
      userProfile: Prisma.$LocalUserProfilePayload<ExtArgs>
      feedItems: Prisma.$FeedItemPayload<ExtArgs>[]
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      userId: string
      feedType: string
      topicSlug: string | null
      lastSyncAt: Date
      nextSyncAt: Date | null
      isStale: boolean
      syncInProgress: boolean
      lastPage: number
      hasMore: boolean
      totalItems: number | null
      syncCount: number
      lastSyncDuration: number | null
      lastError: string | null
      consecutiveErrors: number
      createdAt: Date
      updatedAt: Date
    }, ExtArgs["result"]["feedSync"]>
    composites: {}
  }

  type FeedSyncGetPayload<S extends boolean | null | undefined | FeedSyncDefaultArgs> = $Result.GetResult<Prisma.$FeedSyncPayload, S>

  type FeedSyncCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<FeedSyncFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: FeedSyncCountAggregateInputType | true
    }

  export interface FeedSyncDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['FeedSync'], meta: { name: 'FeedSync' } }
    /**
     * Find zero or one FeedSync that matches the filter.
     * @param {FeedSyncFindUniqueArgs} args - Arguments to find a FeedSync
     * @example
     * // Get one FeedSync
     * const feedSync = await prisma.feedSync.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends FeedSyncFindUniqueArgs>(args: SelectSubset<T, FeedSyncFindUniqueArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one FeedSync that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {FeedSyncFindUniqueOrThrowArgs} args - Arguments to find a FeedSync
     * @example
     * // Get one FeedSync
     * const feedSync = await prisma.feedSync.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends FeedSyncFindUniqueOrThrowArgs>(args: SelectSubset<T, FeedSyncFindUniqueOrThrowArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first FeedSync that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncFindFirstArgs} args - Arguments to find a FeedSync
     * @example
     * // Get one FeedSync
     * const feedSync = await prisma.feedSync.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends FeedSyncFindFirstArgs>(args?: SelectSubset<T, FeedSyncFindFirstArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first FeedSync that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncFindFirstOrThrowArgs} args - Arguments to find a FeedSync
     * @example
     * // Get one FeedSync
     * const feedSync = await prisma.feedSync.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends FeedSyncFindFirstOrThrowArgs>(args?: SelectSubset<T, FeedSyncFindFirstOrThrowArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more FeedSyncs that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all FeedSyncs
     * const feedSyncs = await prisma.feedSync.findMany()
     * 
     * // Get first 10 FeedSyncs
     * const feedSyncs = await prisma.feedSync.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const feedSyncWithIdOnly = await prisma.feedSync.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends FeedSyncFindManyArgs>(args?: SelectSubset<T, FeedSyncFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a FeedSync.
     * @param {FeedSyncCreateArgs} args - Arguments to create a FeedSync.
     * @example
     * // Create one FeedSync
     * const FeedSync = await prisma.feedSync.create({
     *   data: {
     *     // ... data to create a FeedSync
     *   }
     * })
     * 
     */
    create<T extends FeedSyncCreateArgs>(args: SelectSubset<T, FeedSyncCreateArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many FeedSyncs.
     * @param {FeedSyncCreateManyArgs} args - Arguments to create many FeedSyncs.
     * @example
     * // Create many FeedSyncs
     * const feedSync = await prisma.feedSync.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends FeedSyncCreateManyArgs>(args?: SelectSubset<T, FeedSyncCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many FeedSyncs and returns the data saved in the database.
     * @param {FeedSyncCreateManyAndReturnArgs} args - Arguments to create many FeedSyncs.
     * @example
     * // Create many FeedSyncs
     * const feedSync = await prisma.feedSync.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many FeedSyncs and only return the `id`
     * const feedSyncWithIdOnly = await prisma.feedSync.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends FeedSyncCreateManyAndReturnArgs>(args?: SelectSubset<T, FeedSyncCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a FeedSync.
     * @param {FeedSyncDeleteArgs} args - Arguments to delete one FeedSync.
     * @example
     * // Delete one FeedSync
     * const FeedSync = await prisma.feedSync.delete({
     *   where: {
     *     // ... filter to delete one FeedSync
     *   }
     * })
     * 
     */
    delete<T extends FeedSyncDeleteArgs>(args: SelectSubset<T, FeedSyncDeleteArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one FeedSync.
     * @param {FeedSyncUpdateArgs} args - Arguments to update one FeedSync.
     * @example
     * // Update one FeedSync
     * const feedSync = await prisma.feedSync.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends FeedSyncUpdateArgs>(args: SelectSubset<T, FeedSyncUpdateArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more FeedSyncs.
     * @param {FeedSyncDeleteManyArgs} args - Arguments to filter FeedSyncs to delete.
     * @example
     * // Delete a few FeedSyncs
     * const { count } = await prisma.feedSync.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends FeedSyncDeleteManyArgs>(args?: SelectSubset<T, FeedSyncDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more FeedSyncs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many FeedSyncs
     * const feedSync = await prisma.feedSync.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends FeedSyncUpdateManyArgs>(args: SelectSubset<T, FeedSyncUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more FeedSyncs and returns the data updated in the database.
     * @param {FeedSyncUpdateManyAndReturnArgs} args - Arguments to update many FeedSyncs.
     * @example
     * // Update many FeedSyncs
     * const feedSync = await prisma.feedSync.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more FeedSyncs and only return the `id`
     * const feedSyncWithIdOnly = await prisma.feedSync.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends FeedSyncUpdateManyAndReturnArgs>(args: SelectSubset<T, FeedSyncUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one FeedSync.
     * @param {FeedSyncUpsertArgs} args - Arguments to update or create a FeedSync.
     * @example
     * // Update or create a FeedSync
     * const feedSync = await prisma.feedSync.upsert({
     *   create: {
     *     // ... data to create a FeedSync
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the FeedSync we want to update
     *   }
     * })
     */
    upsert<T extends FeedSyncUpsertArgs>(args: SelectSubset<T, FeedSyncUpsertArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of FeedSyncs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncCountArgs} args - Arguments to filter FeedSyncs to count.
     * @example
     * // Count the number of FeedSyncs
     * const count = await prisma.feedSync.count({
     *   where: {
     *     // ... the filter for the FeedSyncs we want to count
     *   }
     * })
    **/
    count<T extends FeedSyncCountArgs>(
      args?: Subset<T, FeedSyncCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], FeedSyncCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a FeedSync.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends FeedSyncAggregateArgs>(args: Subset<T, FeedSyncAggregateArgs>): Prisma.PrismaPromise<GetFeedSyncAggregateType<T>>

    /**
     * Group by FeedSync.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedSyncGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends FeedSyncGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: FeedSyncGroupByArgs['orderBy'] }
        : { orderBy?: FeedSyncGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, FeedSyncGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetFeedSyncGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the FeedSync model
   */
  readonly fields: FeedSyncFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for FeedSync.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__FeedSyncClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    userProfile<T extends LocalUserProfileDefaultArgs<ExtArgs> = {}>(args?: Subset<T, LocalUserProfileDefaultArgs<ExtArgs>>): Prisma__LocalUserProfileClient<$Result.GetResult<Prisma.$LocalUserProfilePayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    feedItems<T extends FeedSync$feedItemsArgs<ExtArgs> = {}>(args?: Subset<T, FeedSync$feedItemsArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findMany", GlobalOmitOptions> | Null>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the FeedSync model
   */
  interface FeedSyncFieldRefs {
    readonly id: FieldRef<"FeedSync", 'String'>
    readonly userId: FieldRef<"FeedSync", 'String'>
    readonly feedType: FieldRef<"FeedSync", 'String'>
    readonly topicSlug: FieldRef<"FeedSync", 'String'>
    readonly lastSyncAt: FieldRef<"FeedSync", 'DateTime'>
    readonly nextSyncAt: FieldRef<"FeedSync", 'DateTime'>
    readonly isStale: FieldRef<"FeedSync", 'Boolean'>
    readonly syncInProgress: FieldRef<"FeedSync", 'Boolean'>
    readonly lastPage: FieldRef<"FeedSync", 'Int'>
    readonly hasMore: FieldRef<"FeedSync", 'Boolean'>
    readonly totalItems: FieldRef<"FeedSync", 'Int'>
    readonly syncCount: FieldRef<"FeedSync", 'Int'>
    readonly lastSyncDuration: FieldRef<"FeedSync", 'Int'>
    readonly lastError: FieldRef<"FeedSync", 'String'>
    readonly consecutiveErrors: FieldRef<"FeedSync", 'Int'>
    readonly createdAt: FieldRef<"FeedSync", 'DateTime'>
    readonly updatedAt: FieldRef<"FeedSync", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * FeedSync findUnique
   */
  export type FeedSyncFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * Filter, which FeedSync to fetch.
     */
    where: FeedSyncWhereUniqueInput
  }

  /**
   * FeedSync findUniqueOrThrow
   */
  export type FeedSyncFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * Filter, which FeedSync to fetch.
     */
    where: FeedSyncWhereUniqueInput
  }

  /**
   * FeedSync findFirst
   */
  export type FeedSyncFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * Filter, which FeedSync to fetch.
     */
    where?: FeedSyncWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedSyncs to fetch.
     */
    orderBy?: FeedSyncOrderByWithRelationInput | FeedSyncOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for FeedSyncs.
     */
    cursor?: FeedSyncWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedSyncs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedSyncs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of FeedSyncs.
     */
    distinct?: FeedSyncScalarFieldEnum | FeedSyncScalarFieldEnum[]
  }

  /**
   * FeedSync findFirstOrThrow
   */
  export type FeedSyncFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * Filter, which FeedSync to fetch.
     */
    where?: FeedSyncWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedSyncs to fetch.
     */
    orderBy?: FeedSyncOrderByWithRelationInput | FeedSyncOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for FeedSyncs.
     */
    cursor?: FeedSyncWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedSyncs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedSyncs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of FeedSyncs.
     */
    distinct?: FeedSyncScalarFieldEnum | FeedSyncScalarFieldEnum[]
  }

  /**
   * FeedSync findMany
   */
  export type FeedSyncFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * Filter, which FeedSyncs to fetch.
     */
    where?: FeedSyncWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedSyncs to fetch.
     */
    orderBy?: FeedSyncOrderByWithRelationInput | FeedSyncOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing FeedSyncs.
     */
    cursor?: FeedSyncWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedSyncs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedSyncs.
     */
    skip?: number
    distinct?: FeedSyncScalarFieldEnum | FeedSyncScalarFieldEnum[]
  }

  /**
   * FeedSync create
   */
  export type FeedSyncCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * The data needed to create a FeedSync.
     */
    data: XOR<FeedSyncCreateInput, FeedSyncUncheckedCreateInput>
  }

  /**
   * FeedSync createMany
   */
  export type FeedSyncCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many FeedSyncs.
     */
    data: FeedSyncCreateManyInput | FeedSyncCreateManyInput[]
  }

  /**
   * FeedSync createManyAndReturn
   */
  export type FeedSyncCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * The data used to create many FeedSyncs.
     */
    data: FeedSyncCreateManyInput | FeedSyncCreateManyInput[]
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * FeedSync update
   */
  export type FeedSyncUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * The data needed to update a FeedSync.
     */
    data: XOR<FeedSyncUpdateInput, FeedSyncUncheckedUpdateInput>
    /**
     * Choose, which FeedSync to update.
     */
    where: FeedSyncWhereUniqueInput
  }

  /**
   * FeedSync updateMany
   */
  export type FeedSyncUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update FeedSyncs.
     */
    data: XOR<FeedSyncUpdateManyMutationInput, FeedSyncUncheckedUpdateManyInput>
    /**
     * Filter which FeedSyncs to update
     */
    where?: FeedSyncWhereInput
    /**
     * Limit how many FeedSyncs to update.
     */
    limit?: number
  }

  /**
   * FeedSync updateManyAndReturn
   */
  export type FeedSyncUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * The data used to update FeedSyncs.
     */
    data: XOR<FeedSyncUpdateManyMutationInput, FeedSyncUncheckedUpdateManyInput>
    /**
     * Filter which FeedSyncs to update
     */
    where?: FeedSyncWhereInput
    /**
     * Limit how many FeedSyncs to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * FeedSync upsert
   */
  export type FeedSyncUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * The filter to search for the FeedSync to update in case it exists.
     */
    where: FeedSyncWhereUniqueInput
    /**
     * In case the FeedSync found by the `where` argument doesn't exist, create a new FeedSync with this data.
     */
    create: XOR<FeedSyncCreateInput, FeedSyncUncheckedCreateInput>
    /**
     * In case the FeedSync was found with the provided `where` argument, update it with this data.
     */
    update: XOR<FeedSyncUpdateInput, FeedSyncUncheckedUpdateInput>
  }

  /**
   * FeedSync delete
   */
  export type FeedSyncDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
    /**
     * Filter which FeedSync to delete.
     */
    where: FeedSyncWhereUniqueInput
  }

  /**
   * FeedSync deleteMany
   */
  export type FeedSyncDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which FeedSyncs to delete
     */
    where?: FeedSyncWhereInput
    /**
     * Limit how many FeedSyncs to delete.
     */
    limit?: number
  }

  /**
   * FeedSync.feedItems
   */
  export type FeedSync$feedItemsArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    where?: FeedItemWhereInput
    orderBy?: FeedItemOrderByWithRelationInput | FeedItemOrderByWithRelationInput[]
    cursor?: FeedItemWhereUniqueInput
    take?: number
    skip?: number
    distinct?: FeedItemScalarFieldEnum | FeedItemScalarFieldEnum[]
  }

  /**
   * FeedSync without action
   */
  export type FeedSyncDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedSync
     */
    select?: FeedSyncSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedSync
     */
    omit?: FeedSyncOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedSyncInclude<ExtArgs> | null
  }


  /**
   * Model FeedItem
   */

  export type AggregateFeedItem = {
    _count: FeedItemCountAggregateOutputType | null
    _avg: FeedItemAvgAggregateOutputType | null
    _sum: FeedItemSumAggregateOutputType | null
    _min: FeedItemMinAggregateOutputType | null
    _max: FeedItemMaxAggregateOutputType | null
  }

  export type FeedItemAvgAggregateOutputType = {
    position: number | null
    relevanceScore: number | null
  }

  export type FeedItemSumAggregateOutputType = {
    position: number | null
    relevanceScore: number | null
  }

  export type FeedItemMinAggregateOutputType = {
    id: string | null
    feedSyncId: string | null
    articleId: string | null
    position: number | null
    relevanceScore: number | null
    addedAt: Date | null
  }

  export type FeedItemMaxAggregateOutputType = {
    id: string | null
    feedSyncId: string | null
    articleId: string | null
    position: number | null
    relevanceScore: number | null
    addedAt: Date | null
  }

  export type FeedItemCountAggregateOutputType = {
    id: number
    feedSyncId: number
    articleId: number
    position: number
    relevanceScore: number
    addedAt: number
    _all: number
  }


  export type FeedItemAvgAggregateInputType = {
    position?: true
    relevanceScore?: true
  }

  export type FeedItemSumAggregateInputType = {
    position?: true
    relevanceScore?: true
  }

  export type FeedItemMinAggregateInputType = {
    id?: true
    feedSyncId?: true
    articleId?: true
    position?: true
    relevanceScore?: true
    addedAt?: true
  }

  export type FeedItemMaxAggregateInputType = {
    id?: true
    feedSyncId?: true
    articleId?: true
    position?: true
    relevanceScore?: true
    addedAt?: true
  }

  export type FeedItemCountAggregateInputType = {
    id?: true
    feedSyncId?: true
    articleId?: true
    position?: true
    relevanceScore?: true
    addedAt?: true
    _all?: true
  }

  export type FeedItemAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which FeedItem to aggregate.
     */
    where?: FeedItemWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedItems to fetch.
     */
    orderBy?: FeedItemOrderByWithRelationInput | FeedItemOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: FeedItemWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedItems from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedItems.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned FeedItems
    **/
    _count?: true | FeedItemCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: FeedItemAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: FeedItemSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: FeedItemMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: FeedItemMaxAggregateInputType
  }

  export type GetFeedItemAggregateType<T extends FeedItemAggregateArgs> = {
        [P in keyof T & keyof AggregateFeedItem]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateFeedItem[P]>
      : GetScalarType<T[P], AggregateFeedItem[P]>
  }




  export type FeedItemGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: FeedItemWhereInput
    orderBy?: FeedItemOrderByWithAggregationInput | FeedItemOrderByWithAggregationInput[]
    by: FeedItemScalarFieldEnum[] | FeedItemScalarFieldEnum
    having?: FeedItemScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: FeedItemCountAggregateInputType | true
    _avg?: FeedItemAvgAggregateInputType
    _sum?: FeedItemSumAggregateInputType
    _min?: FeedItemMinAggregateInputType
    _max?: FeedItemMaxAggregateInputType
  }

  export type FeedItemGroupByOutputType = {
    id: string
    feedSyncId: string
    articleId: string
    position: number
    relevanceScore: number | null
    addedAt: Date
    _count: FeedItemCountAggregateOutputType | null
    _avg: FeedItemAvgAggregateOutputType | null
    _sum: FeedItemSumAggregateOutputType | null
    _min: FeedItemMinAggregateOutputType | null
    _max: FeedItemMaxAggregateOutputType | null
  }

  type GetFeedItemGroupByPayload<T extends FeedItemGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<FeedItemGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof FeedItemGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], FeedItemGroupByOutputType[P]>
            : GetScalarType<T[P], FeedItemGroupByOutputType[P]>
        }
      >
    >


  export type FeedItemSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    feedSyncId?: boolean
    articleId?: boolean
    position?: boolean
    relevanceScore?: boolean
    addedAt?: boolean
    feedSync?: boolean | FeedSyncDefaultArgs<ExtArgs>
    article?: boolean | LocalArticleDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["feedItem"]>

  export type FeedItemSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    feedSyncId?: boolean
    articleId?: boolean
    position?: boolean
    relevanceScore?: boolean
    addedAt?: boolean
    feedSync?: boolean | FeedSyncDefaultArgs<ExtArgs>
    article?: boolean | LocalArticleDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["feedItem"]>

  export type FeedItemSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    feedSyncId?: boolean
    articleId?: boolean
    position?: boolean
    relevanceScore?: boolean
    addedAt?: boolean
    feedSync?: boolean | FeedSyncDefaultArgs<ExtArgs>
    article?: boolean | LocalArticleDefaultArgs<ExtArgs>
  }, ExtArgs["result"]["feedItem"]>

  export type FeedItemSelectScalar = {
    id?: boolean
    feedSyncId?: boolean
    articleId?: boolean
    position?: boolean
    relevanceScore?: boolean
    addedAt?: boolean
  }

  export type FeedItemOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "feedSyncId" | "articleId" | "position" | "relevanceScore" | "addedAt", ExtArgs["result"]["feedItem"]>
  export type FeedItemInclude<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedSync?: boolean | FeedSyncDefaultArgs<ExtArgs>
    article?: boolean | LocalArticleDefaultArgs<ExtArgs>
  }
  export type FeedItemIncludeCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedSync?: boolean | FeedSyncDefaultArgs<ExtArgs>
    article?: boolean | LocalArticleDefaultArgs<ExtArgs>
  }
  export type FeedItemIncludeUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    feedSync?: boolean | FeedSyncDefaultArgs<ExtArgs>
    article?: boolean | LocalArticleDefaultArgs<ExtArgs>
  }

  export type $FeedItemPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "FeedItem"
    objects: {
      feedSync: Prisma.$FeedSyncPayload<ExtArgs>
      article: Prisma.$LocalArticlePayload<ExtArgs>
    }
    scalars: $Extensions.GetPayloadResult<{
      id: string
      feedSyncId: string
      articleId: string
      position: number
      relevanceScore: number | null
      addedAt: Date
    }, ExtArgs["result"]["feedItem"]>
    composites: {}
  }

  type FeedItemGetPayload<S extends boolean | null | undefined | FeedItemDefaultArgs> = $Result.GetResult<Prisma.$FeedItemPayload, S>

  type FeedItemCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<FeedItemFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: FeedItemCountAggregateInputType | true
    }

  export interface FeedItemDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['FeedItem'], meta: { name: 'FeedItem' } }
    /**
     * Find zero or one FeedItem that matches the filter.
     * @param {FeedItemFindUniqueArgs} args - Arguments to find a FeedItem
     * @example
     * // Get one FeedItem
     * const feedItem = await prisma.feedItem.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends FeedItemFindUniqueArgs>(args: SelectSubset<T, FeedItemFindUniqueArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one FeedItem that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {FeedItemFindUniqueOrThrowArgs} args - Arguments to find a FeedItem
     * @example
     * // Get one FeedItem
     * const feedItem = await prisma.feedItem.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends FeedItemFindUniqueOrThrowArgs>(args: SelectSubset<T, FeedItemFindUniqueOrThrowArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first FeedItem that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemFindFirstArgs} args - Arguments to find a FeedItem
     * @example
     * // Get one FeedItem
     * const feedItem = await prisma.feedItem.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends FeedItemFindFirstArgs>(args?: SelectSubset<T, FeedItemFindFirstArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first FeedItem that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemFindFirstOrThrowArgs} args - Arguments to find a FeedItem
     * @example
     * // Get one FeedItem
     * const feedItem = await prisma.feedItem.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends FeedItemFindFirstOrThrowArgs>(args?: SelectSubset<T, FeedItemFindFirstOrThrowArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more FeedItems that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all FeedItems
     * const feedItems = await prisma.feedItem.findMany()
     * 
     * // Get first 10 FeedItems
     * const feedItems = await prisma.feedItem.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const feedItemWithIdOnly = await prisma.feedItem.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends FeedItemFindManyArgs>(args?: SelectSubset<T, FeedItemFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a FeedItem.
     * @param {FeedItemCreateArgs} args - Arguments to create a FeedItem.
     * @example
     * // Create one FeedItem
     * const FeedItem = await prisma.feedItem.create({
     *   data: {
     *     // ... data to create a FeedItem
     *   }
     * })
     * 
     */
    create<T extends FeedItemCreateArgs>(args: SelectSubset<T, FeedItemCreateArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many FeedItems.
     * @param {FeedItemCreateManyArgs} args - Arguments to create many FeedItems.
     * @example
     * // Create many FeedItems
     * const feedItem = await prisma.feedItem.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends FeedItemCreateManyArgs>(args?: SelectSubset<T, FeedItemCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many FeedItems and returns the data saved in the database.
     * @param {FeedItemCreateManyAndReturnArgs} args - Arguments to create many FeedItems.
     * @example
     * // Create many FeedItems
     * const feedItem = await prisma.feedItem.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many FeedItems and only return the `id`
     * const feedItemWithIdOnly = await prisma.feedItem.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends FeedItemCreateManyAndReturnArgs>(args?: SelectSubset<T, FeedItemCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a FeedItem.
     * @param {FeedItemDeleteArgs} args - Arguments to delete one FeedItem.
     * @example
     * // Delete one FeedItem
     * const FeedItem = await prisma.feedItem.delete({
     *   where: {
     *     // ... filter to delete one FeedItem
     *   }
     * })
     * 
     */
    delete<T extends FeedItemDeleteArgs>(args: SelectSubset<T, FeedItemDeleteArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one FeedItem.
     * @param {FeedItemUpdateArgs} args - Arguments to update one FeedItem.
     * @example
     * // Update one FeedItem
     * const feedItem = await prisma.feedItem.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends FeedItemUpdateArgs>(args: SelectSubset<T, FeedItemUpdateArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more FeedItems.
     * @param {FeedItemDeleteManyArgs} args - Arguments to filter FeedItems to delete.
     * @example
     * // Delete a few FeedItems
     * const { count } = await prisma.feedItem.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends FeedItemDeleteManyArgs>(args?: SelectSubset<T, FeedItemDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more FeedItems.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many FeedItems
     * const feedItem = await prisma.feedItem.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends FeedItemUpdateManyArgs>(args: SelectSubset<T, FeedItemUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more FeedItems and returns the data updated in the database.
     * @param {FeedItemUpdateManyAndReturnArgs} args - Arguments to update many FeedItems.
     * @example
     * // Update many FeedItems
     * const feedItem = await prisma.feedItem.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more FeedItems and only return the `id`
     * const feedItemWithIdOnly = await prisma.feedItem.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends FeedItemUpdateManyAndReturnArgs>(args: SelectSubset<T, FeedItemUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one FeedItem.
     * @param {FeedItemUpsertArgs} args - Arguments to update or create a FeedItem.
     * @example
     * // Update or create a FeedItem
     * const feedItem = await prisma.feedItem.upsert({
     *   create: {
     *     // ... data to create a FeedItem
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the FeedItem we want to update
     *   }
     * })
     */
    upsert<T extends FeedItemUpsertArgs>(args: SelectSubset<T, FeedItemUpsertArgs<ExtArgs>>): Prisma__FeedItemClient<$Result.GetResult<Prisma.$FeedItemPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of FeedItems.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemCountArgs} args - Arguments to filter FeedItems to count.
     * @example
     * // Count the number of FeedItems
     * const count = await prisma.feedItem.count({
     *   where: {
     *     // ... the filter for the FeedItems we want to count
     *   }
     * })
    **/
    count<T extends FeedItemCountArgs>(
      args?: Subset<T, FeedItemCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], FeedItemCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a FeedItem.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends FeedItemAggregateArgs>(args: Subset<T, FeedItemAggregateArgs>): Prisma.PrismaPromise<GetFeedItemAggregateType<T>>

    /**
     * Group by FeedItem.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {FeedItemGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends FeedItemGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: FeedItemGroupByArgs['orderBy'] }
        : { orderBy?: FeedItemGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, FeedItemGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetFeedItemGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the FeedItem model
   */
  readonly fields: FeedItemFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for FeedItem.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__FeedItemClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    feedSync<T extends FeedSyncDefaultArgs<ExtArgs> = {}>(args?: Subset<T, FeedSyncDefaultArgs<ExtArgs>>): Prisma__FeedSyncClient<$Result.GetResult<Prisma.$FeedSyncPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    article<T extends LocalArticleDefaultArgs<ExtArgs> = {}>(args?: Subset<T, LocalArticleDefaultArgs<ExtArgs>>): Prisma__LocalArticleClient<$Result.GetResult<Prisma.$LocalArticlePayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions> | Null, Null, ExtArgs, GlobalOmitOptions>
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the FeedItem model
   */
  interface FeedItemFieldRefs {
    readonly id: FieldRef<"FeedItem", 'String'>
    readonly feedSyncId: FieldRef<"FeedItem", 'String'>
    readonly articleId: FieldRef<"FeedItem", 'String'>
    readonly position: FieldRef<"FeedItem", 'Int'>
    readonly relevanceScore: FieldRef<"FeedItem", 'Float'>
    readonly addedAt: FieldRef<"FeedItem", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * FeedItem findUnique
   */
  export type FeedItemFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * Filter, which FeedItem to fetch.
     */
    where: FeedItemWhereUniqueInput
  }

  /**
   * FeedItem findUniqueOrThrow
   */
  export type FeedItemFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * Filter, which FeedItem to fetch.
     */
    where: FeedItemWhereUniqueInput
  }

  /**
   * FeedItem findFirst
   */
  export type FeedItemFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * Filter, which FeedItem to fetch.
     */
    where?: FeedItemWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedItems to fetch.
     */
    orderBy?: FeedItemOrderByWithRelationInput | FeedItemOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for FeedItems.
     */
    cursor?: FeedItemWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedItems from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedItems.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of FeedItems.
     */
    distinct?: FeedItemScalarFieldEnum | FeedItemScalarFieldEnum[]
  }

  /**
   * FeedItem findFirstOrThrow
   */
  export type FeedItemFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * Filter, which FeedItem to fetch.
     */
    where?: FeedItemWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedItems to fetch.
     */
    orderBy?: FeedItemOrderByWithRelationInput | FeedItemOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for FeedItems.
     */
    cursor?: FeedItemWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedItems from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedItems.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of FeedItems.
     */
    distinct?: FeedItemScalarFieldEnum | FeedItemScalarFieldEnum[]
  }

  /**
   * FeedItem findMany
   */
  export type FeedItemFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * Filter, which FeedItems to fetch.
     */
    where?: FeedItemWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of FeedItems to fetch.
     */
    orderBy?: FeedItemOrderByWithRelationInput | FeedItemOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing FeedItems.
     */
    cursor?: FeedItemWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` FeedItems from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` FeedItems.
     */
    skip?: number
    distinct?: FeedItemScalarFieldEnum | FeedItemScalarFieldEnum[]
  }

  /**
   * FeedItem create
   */
  export type FeedItemCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * The data needed to create a FeedItem.
     */
    data: XOR<FeedItemCreateInput, FeedItemUncheckedCreateInput>
  }

  /**
   * FeedItem createMany
   */
  export type FeedItemCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many FeedItems.
     */
    data: FeedItemCreateManyInput | FeedItemCreateManyInput[]
  }

  /**
   * FeedItem createManyAndReturn
   */
  export type FeedItemCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * The data used to create many FeedItems.
     */
    data: FeedItemCreateManyInput | FeedItemCreateManyInput[]
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemIncludeCreateManyAndReturn<ExtArgs> | null
  }

  /**
   * FeedItem update
   */
  export type FeedItemUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * The data needed to update a FeedItem.
     */
    data: XOR<FeedItemUpdateInput, FeedItemUncheckedUpdateInput>
    /**
     * Choose, which FeedItem to update.
     */
    where: FeedItemWhereUniqueInput
  }

  /**
   * FeedItem updateMany
   */
  export type FeedItemUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update FeedItems.
     */
    data: XOR<FeedItemUpdateManyMutationInput, FeedItemUncheckedUpdateManyInput>
    /**
     * Filter which FeedItems to update
     */
    where?: FeedItemWhereInput
    /**
     * Limit how many FeedItems to update.
     */
    limit?: number
  }

  /**
   * FeedItem updateManyAndReturn
   */
  export type FeedItemUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * The data used to update FeedItems.
     */
    data: XOR<FeedItemUpdateManyMutationInput, FeedItemUncheckedUpdateManyInput>
    /**
     * Filter which FeedItems to update
     */
    where?: FeedItemWhereInput
    /**
     * Limit how many FeedItems to update.
     */
    limit?: number
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemIncludeUpdateManyAndReturn<ExtArgs> | null
  }

  /**
   * FeedItem upsert
   */
  export type FeedItemUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * The filter to search for the FeedItem to update in case it exists.
     */
    where: FeedItemWhereUniqueInput
    /**
     * In case the FeedItem found by the `where` argument doesn't exist, create a new FeedItem with this data.
     */
    create: XOR<FeedItemCreateInput, FeedItemUncheckedCreateInput>
    /**
     * In case the FeedItem was found with the provided `where` argument, update it with this data.
     */
    update: XOR<FeedItemUpdateInput, FeedItemUncheckedUpdateInput>
  }

  /**
   * FeedItem delete
   */
  export type FeedItemDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
    /**
     * Filter which FeedItem to delete.
     */
    where: FeedItemWhereUniqueInput
  }

  /**
   * FeedItem deleteMany
   */
  export type FeedItemDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which FeedItems to delete
     */
    where?: FeedItemWhereInput
    /**
     * Limit how many FeedItems to delete.
     */
    limit?: number
  }

  /**
   * FeedItem without action
   */
  export type FeedItemDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the FeedItem
     */
    select?: FeedItemSelect<ExtArgs> | null
    /**
     * Omit specific fields from the FeedItem
     */
    omit?: FeedItemOmit<ExtArgs> | null
    /**
     * Choose, which related nodes to fetch as well
     */
    include?: FeedItemInclude<ExtArgs> | null
  }


  /**
   * Model SyncJob
   */

  export type AggregateSyncJob = {
    _count: SyncJobCountAggregateOutputType | null
    _avg: SyncJobAvgAggregateOutputType | null
    _sum: SyncJobSumAggregateOutputType | null
    _min: SyncJobMinAggregateOutputType | null
    _max: SyncJobMaxAggregateOutputType | null
  }

  export type SyncJobAvgAggregateOutputType = {
    priority: number | null
    attempts: number | null
    maxAttempts: number | null
  }

  export type SyncJobSumAggregateOutputType = {
    priority: number | null
    attempts: number | null
    maxAttempts: number | null
  }

  export type SyncJobMinAggregateOutputType = {
    id: string | null
    type: string | null
    userId: string | null
    feedType: string | null
    topicSlug: string | null
    articleId: string | null
    status: string | null
    priority: number | null
    attempts: number | null
    maxAttempts: number | null
    scheduledAt: Date | null
    startedAt: Date | null
    completedAt: Date | null
    result: string | null
    error: string | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type SyncJobMaxAggregateOutputType = {
    id: string | null
    type: string | null
    userId: string | null
    feedType: string | null
    topicSlug: string | null
    articleId: string | null
    status: string | null
    priority: number | null
    attempts: number | null
    maxAttempts: number | null
    scheduledAt: Date | null
    startedAt: Date | null
    completedAt: Date | null
    result: string | null
    error: string | null
    createdAt: Date | null
    updatedAt: Date | null
  }

  export type SyncJobCountAggregateOutputType = {
    id: number
    type: number
    userId: number
    feedType: number
    topicSlug: number
    articleId: number
    status: number
    priority: number
    attempts: number
    maxAttempts: number
    scheduledAt: number
    startedAt: number
    completedAt: number
    result: number
    error: number
    createdAt: number
    updatedAt: number
    _all: number
  }


  export type SyncJobAvgAggregateInputType = {
    priority?: true
    attempts?: true
    maxAttempts?: true
  }

  export type SyncJobSumAggregateInputType = {
    priority?: true
    attempts?: true
    maxAttempts?: true
  }

  export type SyncJobMinAggregateInputType = {
    id?: true
    type?: true
    userId?: true
    feedType?: true
    topicSlug?: true
    articleId?: true
    status?: true
    priority?: true
    attempts?: true
    maxAttempts?: true
    scheduledAt?: true
    startedAt?: true
    completedAt?: true
    result?: true
    error?: true
    createdAt?: true
    updatedAt?: true
  }

  export type SyncJobMaxAggregateInputType = {
    id?: true
    type?: true
    userId?: true
    feedType?: true
    topicSlug?: true
    articleId?: true
    status?: true
    priority?: true
    attempts?: true
    maxAttempts?: true
    scheduledAt?: true
    startedAt?: true
    completedAt?: true
    result?: true
    error?: true
    createdAt?: true
    updatedAt?: true
  }

  export type SyncJobCountAggregateInputType = {
    id?: true
    type?: true
    userId?: true
    feedType?: true
    topicSlug?: true
    articleId?: true
    status?: true
    priority?: true
    attempts?: true
    maxAttempts?: true
    scheduledAt?: true
    startedAt?: true
    completedAt?: true
    result?: true
    error?: true
    createdAt?: true
    updatedAt?: true
    _all?: true
  }

  export type SyncJobAggregateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which SyncJob to aggregate.
     */
    where?: SyncJobWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of SyncJobs to fetch.
     */
    orderBy?: SyncJobOrderByWithRelationInput | SyncJobOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the start position
     */
    cursor?: SyncJobWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` SyncJobs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` SyncJobs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Count returned SyncJobs
    **/
    _count?: true | SyncJobCountAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to average
    **/
    _avg?: SyncJobAvgAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to sum
    **/
    _sum?: SyncJobSumAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the minimum value
    **/
    _min?: SyncJobMinAggregateInputType
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/aggregations Aggregation Docs}
     * 
     * Select which fields to find the maximum value
    **/
    _max?: SyncJobMaxAggregateInputType
  }

  export type GetSyncJobAggregateType<T extends SyncJobAggregateArgs> = {
        [P in keyof T & keyof AggregateSyncJob]: P extends '_count' | 'count'
      ? T[P] extends true
        ? number
        : GetScalarType<T[P], AggregateSyncJob[P]>
      : GetScalarType<T[P], AggregateSyncJob[P]>
  }




  export type SyncJobGroupByArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    where?: SyncJobWhereInput
    orderBy?: SyncJobOrderByWithAggregationInput | SyncJobOrderByWithAggregationInput[]
    by: SyncJobScalarFieldEnum[] | SyncJobScalarFieldEnum
    having?: SyncJobScalarWhereWithAggregatesInput
    take?: number
    skip?: number
    _count?: SyncJobCountAggregateInputType | true
    _avg?: SyncJobAvgAggregateInputType
    _sum?: SyncJobSumAggregateInputType
    _min?: SyncJobMinAggregateInputType
    _max?: SyncJobMaxAggregateInputType
  }

  export type SyncJobGroupByOutputType = {
    id: string
    type: string
    userId: string | null
    feedType: string | null
    topicSlug: string | null
    articleId: string | null
    status: string
    priority: number
    attempts: number
    maxAttempts: number
    scheduledAt: Date
    startedAt: Date | null
    completedAt: Date | null
    result: string | null
    error: string | null
    createdAt: Date
    updatedAt: Date
    _count: SyncJobCountAggregateOutputType | null
    _avg: SyncJobAvgAggregateOutputType | null
    _sum: SyncJobSumAggregateOutputType | null
    _min: SyncJobMinAggregateOutputType | null
    _max: SyncJobMaxAggregateOutputType | null
  }

  type GetSyncJobGroupByPayload<T extends SyncJobGroupByArgs> = Prisma.PrismaPromise<
    Array<
      PickEnumerable<SyncJobGroupByOutputType, T['by']> &
        {
          [P in ((keyof T) & (keyof SyncJobGroupByOutputType))]: P extends '_count'
            ? T[P] extends boolean
              ? number
              : GetScalarType<T[P], SyncJobGroupByOutputType[P]>
            : GetScalarType<T[P], SyncJobGroupByOutputType[P]>
        }
      >
    >


  export type SyncJobSelect<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    type?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    articleId?: boolean
    status?: boolean
    priority?: boolean
    attempts?: boolean
    maxAttempts?: boolean
    scheduledAt?: boolean
    startedAt?: boolean
    completedAt?: boolean
    result?: boolean
    error?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["syncJob"]>

  export type SyncJobSelectCreateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    type?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    articleId?: boolean
    status?: boolean
    priority?: boolean
    attempts?: boolean
    maxAttempts?: boolean
    scheduledAt?: boolean
    startedAt?: boolean
    completedAt?: boolean
    result?: boolean
    error?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["syncJob"]>

  export type SyncJobSelectUpdateManyAndReturn<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetSelect<{
    id?: boolean
    type?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    articleId?: boolean
    status?: boolean
    priority?: boolean
    attempts?: boolean
    maxAttempts?: boolean
    scheduledAt?: boolean
    startedAt?: boolean
    completedAt?: boolean
    result?: boolean
    error?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }, ExtArgs["result"]["syncJob"]>

  export type SyncJobSelectScalar = {
    id?: boolean
    type?: boolean
    userId?: boolean
    feedType?: boolean
    topicSlug?: boolean
    articleId?: boolean
    status?: boolean
    priority?: boolean
    attempts?: boolean
    maxAttempts?: boolean
    scheduledAt?: boolean
    startedAt?: boolean
    completedAt?: boolean
    result?: boolean
    error?: boolean
    createdAt?: boolean
    updatedAt?: boolean
  }

  export type SyncJobOmit<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = $Extensions.GetOmit<"id" | "type" | "userId" | "feedType" | "topicSlug" | "articleId" | "status" | "priority" | "attempts" | "maxAttempts" | "scheduledAt" | "startedAt" | "completedAt" | "result" | "error" | "createdAt" | "updatedAt", ExtArgs["result"]["syncJob"]>

  export type $SyncJobPayload<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    name: "SyncJob"
    objects: {}
    scalars: $Extensions.GetPayloadResult<{
      id: string
      type: string
      userId: string | null
      feedType: string | null
      topicSlug: string | null
      articleId: string | null
      status: string
      priority: number
      attempts: number
      maxAttempts: number
      scheduledAt: Date
      startedAt: Date | null
      completedAt: Date | null
      result: string | null
      error: string | null
      createdAt: Date
      updatedAt: Date
    }, ExtArgs["result"]["syncJob"]>
    composites: {}
  }

  type SyncJobGetPayload<S extends boolean | null | undefined | SyncJobDefaultArgs> = $Result.GetResult<Prisma.$SyncJobPayload, S>

  type SyncJobCountArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> =
    Omit<SyncJobFindManyArgs, 'select' | 'include' | 'distinct' | 'omit'> & {
      select?: SyncJobCountAggregateInputType | true
    }

  export interface SyncJobDelegate<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> {
    [K: symbol]: { types: Prisma.TypeMap<ExtArgs>['model']['SyncJob'], meta: { name: 'SyncJob' } }
    /**
     * Find zero or one SyncJob that matches the filter.
     * @param {SyncJobFindUniqueArgs} args - Arguments to find a SyncJob
     * @example
     * // Get one SyncJob
     * const syncJob = await prisma.syncJob.findUnique({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUnique<T extends SyncJobFindUniqueArgs>(args: SelectSubset<T, SyncJobFindUniqueArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "findUnique", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find one SyncJob that matches the filter or throw an error with `error.code='P2025'`
     * if no matches were found.
     * @param {SyncJobFindUniqueOrThrowArgs} args - Arguments to find a SyncJob
     * @example
     * // Get one SyncJob
     * const syncJob = await prisma.syncJob.findUniqueOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findUniqueOrThrow<T extends SyncJobFindUniqueOrThrowArgs>(args: SelectSubset<T, SyncJobFindUniqueOrThrowArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "findUniqueOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first SyncJob that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobFindFirstArgs} args - Arguments to find a SyncJob
     * @example
     * // Get one SyncJob
     * const syncJob = await prisma.syncJob.findFirst({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirst<T extends SyncJobFindFirstArgs>(args?: SelectSubset<T, SyncJobFindFirstArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "findFirst", GlobalOmitOptions> | null, null, ExtArgs, GlobalOmitOptions>

    /**
     * Find the first SyncJob that matches the filter or
     * throw `PrismaKnownClientError` with `P2025` code if no matches were found.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobFindFirstOrThrowArgs} args - Arguments to find a SyncJob
     * @example
     * // Get one SyncJob
     * const syncJob = await prisma.syncJob.findFirstOrThrow({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     */
    findFirstOrThrow<T extends SyncJobFindFirstOrThrowArgs>(args?: SelectSubset<T, SyncJobFindFirstOrThrowArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "findFirstOrThrow", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Find zero or more SyncJobs that matches the filter.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobFindManyArgs} args - Arguments to filter and select certain fields only.
     * @example
     * // Get all SyncJobs
     * const syncJobs = await prisma.syncJob.findMany()
     * 
     * // Get first 10 SyncJobs
     * const syncJobs = await prisma.syncJob.findMany({ take: 10 })
     * 
     * // Only select the `id`
     * const syncJobWithIdOnly = await prisma.syncJob.findMany({ select: { id: true } })
     * 
     */
    findMany<T extends SyncJobFindManyArgs>(args?: SelectSubset<T, SyncJobFindManyArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "findMany", GlobalOmitOptions>>

    /**
     * Create a SyncJob.
     * @param {SyncJobCreateArgs} args - Arguments to create a SyncJob.
     * @example
     * // Create one SyncJob
     * const SyncJob = await prisma.syncJob.create({
     *   data: {
     *     // ... data to create a SyncJob
     *   }
     * })
     * 
     */
    create<T extends SyncJobCreateArgs>(args: SelectSubset<T, SyncJobCreateArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "create", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Create many SyncJobs.
     * @param {SyncJobCreateManyArgs} args - Arguments to create many SyncJobs.
     * @example
     * // Create many SyncJobs
     * const syncJob = await prisma.syncJob.createMany({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     *     
     */
    createMany<T extends SyncJobCreateManyArgs>(args?: SelectSubset<T, SyncJobCreateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Create many SyncJobs and returns the data saved in the database.
     * @param {SyncJobCreateManyAndReturnArgs} args - Arguments to create many SyncJobs.
     * @example
     * // Create many SyncJobs
     * const syncJob = await prisma.syncJob.createManyAndReturn({
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Create many SyncJobs and only return the `id`
     * const syncJobWithIdOnly = await prisma.syncJob.createManyAndReturn({
     *   select: { id: true },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    createManyAndReturn<T extends SyncJobCreateManyAndReturnArgs>(args?: SelectSubset<T, SyncJobCreateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "createManyAndReturn", GlobalOmitOptions>>

    /**
     * Delete a SyncJob.
     * @param {SyncJobDeleteArgs} args - Arguments to delete one SyncJob.
     * @example
     * // Delete one SyncJob
     * const SyncJob = await prisma.syncJob.delete({
     *   where: {
     *     // ... filter to delete one SyncJob
     *   }
     * })
     * 
     */
    delete<T extends SyncJobDeleteArgs>(args: SelectSubset<T, SyncJobDeleteArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "delete", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Update one SyncJob.
     * @param {SyncJobUpdateArgs} args - Arguments to update one SyncJob.
     * @example
     * // Update one SyncJob
     * const syncJob = await prisma.syncJob.update({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    update<T extends SyncJobUpdateArgs>(args: SelectSubset<T, SyncJobUpdateArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "update", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>

    /**
     * Delete zero or more SyncJobs.
     * @param {SyncJobDeleteManyArgs} args - Arguments to filter SyncJobs to delete.
     * @example
     * // Delete a few SyncJobs
     * const { count } = await prisma.syncJob.deleteMany({
     *   where: {
     *     // ... provide filter here
     *   }
     * })
     * 
     */
    deleteMany<T extends SyncJobDeleteManyArgs>(args?: SelectSubset<T, SyncJobDeleteManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more SyncJobs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobUpdateManyArgs} args - Arguments to update one or more rows.
     * @example
     * // Update many SyncJobs
     * const syncJob = await prisma.syncJob.updateMany({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: {
     *     // ... provide data here
     *   }
     * })
     * 
     */
    updateMany<T extends SyncJobUpdateManyArgs>(args: SelectSubset<T, SyncJobUpdateManyArgs<ExtArgs>>): Prisma.PrismaPromise<BatchPayload>

    /**
     * Update zero or more SyncJobs and returns the data updated in the database.
     * @param {SyncJobUpdateManyAndReturnArgs} args - Arguments to update many SyncJobs.
     * @example
     * // Update many SyncJobs
     * const syncJob = await prisma.syncJob.updateManyAndReturn({
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * 
     * // Update zero or more SyncJobs and only return the `id`
     * const syncJobWithIdOnly = await prisma.syncJob.updateManyAndReturn({
     *   select: { id: true },
     *   where: {
     *     // ... provide filter here
     *   },
     *   data: [
     *     // ... provide data here
     *   ]
     * })
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * 
     */
    updateManyAndReturn<T extends SyncJobUpdateManyAndReturnArgs>(args: SelectSubset<T, SyncJobUpdateManyAndReturnArgs<ExtArgs>>): Prisma.PrismaPromise<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "updateManyAndReturn", GlobalOmitOptions>>

    /**
     * Create or update one SyncJob.
     * @param {SyncJobUpsertArgs} args - Arguments to update or create a SyncJob.
     * @example
     * // Update or create a SyncJob
     * const syncJob = await prisma.syncJob.upsert({
     *   create: {
     *     // ... data to create a SyncJob
     *   },
     *   update: {
     *     // ... in case it already exists, update
     *   },
     *   where: {
     *     // ... the filter for the SyncJob we want to update
     *   }
     * })
     */
    upsert<T extends SyncJobUpsertArgs>(args: SelectSubset<T, SyncJobUpsertArgs<ExtArgs>>): Prisma__SyncJobClient<$Result.GetResult<Prisma.$SyncJobPayload<ExtArgs>, T, "upsert", GlobalOmitOptions>, never, ExtArgs, GlobalOmitOptions>


    /**
     * Count the number of SyncJobs.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobCountArgs} args - Arguments to filter SyncJobs to count.
     * @example
     * // Count the number of SyncJobs
     * const count = await prisma.syncJob.count({
     *   where: {
     *     // ... the filter for the SyncJobs we want to count
     *   }
     * })
    **/
    count<T extends SyncJobCountArgs>(
      args?: Subset<T, SyncJobCountArgs>,
    ): Prisma.PrismaPromise<
      T extends $Utils.Record<'select', any>
        ? T['select'] extends true
          ? number
          : GetScalarType<T['select'], SyncJobCountAggregateOutputType>
        : number
    >

    /**
     * Allows you to perform aggregations operations on a SyncJob.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobAggregateArgs} args - Select which aggregations you would like to apply and on what fields.
     * @example
     * // Ordered by age ascending
     * // Where email contains prisma.io
     * // Limited to the 10 users
     * const aggregations = await prisma.user.aggregate({
     *   _avg: {
     *     age: true,
     *   },
     *   where: {
     *     email: {
     *       contains: "prisma.io",
     *     },
     *   },
     *   orderBy: {
     *     age: "asc",
     *   },
     *   take: 10,
     * })
    **/
    aggregate<T extends SyncJobAggregateArgs>(args: Subset<T, SyncJobAggregateArgs>): Prisma.PrismaPromise<GetSyncJobAggregateType<T>>

    /**
     * Group by SyncJob.
     * Note, that providing `undefined` is treated as the value not being there.
     * Read more here: https://pris.ly/d/null-undefined
     * @param {SyncJobGroupByArgs} args - Group by arguments.
     * @example
     * // Group by city, order by createdAt, get count
     * const result = await prisma.user.groupBy({
     *   by: ['city', 'createdAt'],
     *   orderBy: {
     *     createdAt: true
     *   },
     *   _count: {
     *     _all: true
     *   },
     * })
     * 
    **/
    groupBy<
      T extends SyncJobGroupByArgs,
      HasSelectOrTake extends Or<
        Extends<'skip', Keys<T>>,
        Extends<'take', Keys<T>>
      >,
      OrderByArg extends True extends HasSelectOrTake
        ? { orderBy: SyncJobGroupByArgs['orderBy'] }
        : { orderBy?: SyncJobGroupByArgs['orderBy'] },
      OrderFields extends ExcludeUnderscoreKeys<Keys<MaybeTupleToUnion<T['orderBy']>>>,
      ByFields extends MaybeTupleToUnion<T['by']>,
      ByValid extends Has<ByFields, OrderFields>,
      HavingFields extends GetHavingFields<T['having']>,
      HavingValid extends Has<ByFields, HavingFields>,
      ByEmpty extends T['by'] extends never[] ? True : False,
      InputErrors extends ByEmpty extends True
      ? `Error: "by" must not be empty.`
      : HavingValid extends False
      ? {
          [P in HavingFields]: P extends ByFields
            ? never
            : P extends string
            ? `Error: Field "${P}" used in "having" needs to be provided in "by".`
            : [
                Error,
                'Field ',
                P,
                ` in "having" needs to be provided in "by"`,
              ]
        }[HavingFields]
      : 'take' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "take", you also need to provide "orderBy"'
      : 'skip' extends Keys<T>
      ? 'orderBy' extends Keys<T>
        ? ByValid extends True
          ? {}
          : {
              [P in OrderFields]: P extends ByFields
                ? never
                : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
            }[OrderFields]
        : 'Error: If you provide "skip", you also need to provide "orderBy"'
      : ByValid extends True
      ? {}
      : {
          [P in OrderFields]: P extends ByFields
            ? never
            : `Error: Field "${P}" in "orderBy" needs to be provided in "by"`
        }[OrderFields]
    >(args: SubsetIntersection<T, SyncJobGroupByArgs, OrderByArg> & InputErrors): {} extends InputErrors ? GetSyncJobGroupByPayload<T> : Prisma.PrismaPromise<InputErrors>
  /**
   * Fields of the SyncJob model
   */
  readonly fields: SyncJobFieldRefs;
  }

  /**
   * The delegate class that acts as a "Promise-like" for SyncJob.
   * Why is this prefixed with `Prisma__`?
   * Because we want to prevent naming conflicts as mentioned in
   * https://github.com/prisma/prisma-client-js/issues/707
   */
  export interface Prisma__SyncJobClient<T, Null = never, ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs, GlobalOmitOptions = {}> extends Prisma.PrismaPromise<T> {
    readonly [Symbol.toStringTag]: "PrismaPromise"
    /**
     * Attaches callbacks for the resolution and/or rejection of the Promise.
     * @param onfulfilled The callback to execute when the Promise is resolved.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of which ever callback is executed.
     */
    then<TResult1 = T, TResult2 = never>(onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null): $Utils.JsPromise<TResult1 | TResult2>
    /**
     * Attaches a callback for only the rejection of the Promise.
     * @param onrejected The callback to execute when the Promise is rejected.
     * @returns A Promise for the completion of the callback.
     */
    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): $Utils.JsPromise<T | TResult>
    /**
     * Attaches a callback that is invoked when the Promise is settled (fulfilled or rejected). The
     * resolved value cannot be modified from the callback.
     * @param onfinally The callback to execute when the Promise is settled (fulfilled or rejected).
     * @returns A Promise for the completion of the callback.
     */
    finally(onfinally?: (() => void) | undefined | null): $Utils.JsPromise<T>
  }




  /**
   * Fields of the SyncJob model
   */
  interface SyncJobFieldRefs {
    readonly id: FieldRef<"SyncJob", 'String'>
    readonly type: FieldRef<"SyncJob", 'String'>
    readonly userId: FieldRef<"SyncJob", 'String'>
    readonly feedType: FieldRef<"SyncJob", 'String'>
    readonly topicSlug: FieldRef<"SyncJob", 'String'>
    readonly articleId: FieldRef<"SyncJob", 'String'>
    readonly status: FieldRef<"SyncJob", 'String'>
    readonly priority: FieldRef<"SyncJob", 'Int'>
    readonly attempts: FieldRef<"SyncJob", 'Int'>
    readonly maxAttempts: FieldRef<"SyncJob", 'Int'>
    readonly scheduledAt: FieldRef<"SyncJob", 'DateTime'>
    readonly startedAt: FieldRef<"SyncJob", 'DateTime'>
    readonly completedAt: FieldRef<"SyncJob", 'DateTime'>
    readonly result: FieldRef<"SyncJob", 'String'>
    readonly error: FieldRef<"SyncJob", 'String'>
    readonly createdAt: FieldRef<"SyncJob", 'DateTime'>
    readonly updatedAt: FieldRef<"SyncJob", 'DateTime'>
  }
    

  // Custom InputTypes
  /**
   * SyncJob findUnique
   */
  export type SyncJobFindUniqueArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * Filter, which SyncJob to fetch.
     */
    where: SyncJobWhereUniqueInput
  }

  /**
   * SyncJob findUniqueOrThrow
   */
  export type SyncJobFindUniqueOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * Filter, which SyncJob to fetch.
     */
    where: SyncJobWhereUniqueInput
  }

  /**
   * SyncJob findFirst
   */
  export type SyncJobFindFirstArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * Filter, which SyncJob to fetch.
     */
    where?: SyncJobWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of SyncJobs to fetch.
     */
    orderBy?: SyncJobOrderByWithRelationInput | SyncJobOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for SyncJobs.
     */
    cursor?: SyncJobWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` SyncJobs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` SyncJobs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of SyncJobs.
     */
    distinct?: SyncJobScalarFieldEnum | SyncJobScalarFieldEnum[]
  }

  /**
   * SyncJob findFirstOrThrow
   */
  export type SyncJobFindFirstOrThrowArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * Filter, which SyncJob to fetch.
     */
    where?: SyncJobWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of SyncJobs to fetch.
     */
    orderBy?: SyncJobOrderByWithRelationInput | SyncJobOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for searching for SyncJobs.
     */
    cursor?: SyncJobWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` SyncJobs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` SyncJobs.
     */
    skip?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/distinct Distinct Docs}
     * 
     * Filter by unique combinations of SyncJobs.
     */
    distinct?: SyncJobScalarFieldEnum | SyncJobScalarFieldEnum[]
  }

  /**
   * SyncJob findMany
   */
  export type SyncJobFindManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * Filter, which SyncJobs to fetch.
     */
    where?: SyncJobWhereInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/sorting Sorting Docs}
     * 
     * Determine the order of SyncJobs to fetch.
     */
    orderBy?: SyncJobOrderByWithRelationInput | SyncJobOrderByWithRelationInput[]
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination#cursor-based-pagination Cursor Docs}
     * 
     * Sets the position for listing SyncJobs.
     */
    cursor?: SyncJobWhereUniqueInput
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Take `±n` SyncJobs from the position of the cursor.
     */
    take?: number
    /**
     * {@link https://www.prisma.io/docs/concepts/components/prisma-client/pagination Pagination Docs}
     * 
     * Skip the first `n` SyncJobs.
     */
    skip?: number
    distinct?: SyncJobScalarFieldEnum | SyncJobScalarFieldEnum[]
  }

  /**
   * SyncJob create
   */
  export type SyncJobCreateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * The data needed to create a SyncJob.
     */
    data: XOR<SyncJobCreateInput, SyncJobUncheckedCreateInput>
  }

  /**
   * SyncJob createMany
   */
  export type SyncJobCreateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to create many SyncJobs.
     */
    data: SyncJobCreateManyInput | SyncJobCreateManyInput[]
  }

  /**
   * SyncJob createManyAndReturn
   */
  export type SyncJobCreateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelectCreateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * The data used to create many SyncJobs.
     */
    data: SyncJobCreateManyInput | SyncJobCreateManyInput[]
  }

  /**
   * SyncJob update
   */
  export type SyncJobUpdateArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * The data needed to update a SyncJob.
     */
    data: XOR<SyncJobUpdateInput, SyncJobUncheckedUpdateInput>
    /**
     * Choose, which SyncJob to update.
     */
    where: SyncJobWhereUniqueInput
  }

  /**
   * SyncJob updateMany
   */
  export type SyncJobUpdateManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * The data used to update SyncJobs.
     */
    data: XOR<SyncJobUpdateManyMutationInput, SyncJobUncheckedUpdateManyInput>
    /**
     * Filter which SyncJobs to update
     */
    where?: SyncJobWhereInput
    /**
     * Limit how many SyncJobs to update.
     */
    limit?: number
  }

  /**
   * SyncJob updateManyAndReturn
   */
  export type SyncJobUpdateManyAndReturnArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelectUpdateManyAndReturn<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * The data used to update SyncJobs.
     */
    data: XOR<SyncJobUpdateManyMutationInput, SyncJobUncheckedUpdateManyInput>
    /**
     * Filter which SyncJobs to update
     */
    where?: SyncJobWhereInput
    /**
     * Limit how many SyncJobs to update.
     */
    limit?: number
  }

  /**
   * SyncJob upsert
   */
  export type SyncJobUpsertArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * The filter to search for the SyncJob to update in case it exists.
     */
    where: SyncJobWhereUniqueInput
    /**
     * In case the SyncJob found by the `where` argument doesn't exist, create a new SyncJob with this data.
     */
    create: XOR<SyncJobCreateInput, SyncJobUncheckedCreateInput>
    /**
     * In case the SyncJob was found with the provided `where` argument, update it with this data.
     */
    update: XOR<SyncJobUpdateInput, SyncJobUncheckedUpdateInput>
  }

  /**
   * SyncJob delete
   */
  export type SyncJobDeleteArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
    /**
     * Filter which SyncJob to delete.
     */
    where: SyncJobWhereUniqueInput
  }

  /**
   * SyncJob deleteMany
   */
  export type SyncJobDeleteManyArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Filter which SyncJobs to delete
     */
    where?: SyncJobWhereInput
    /**
     * Limit how many SyncJobs to delete.
     */
    limit?: number
  }

  /**
   * SyncJob without action
   */
  export type SyncJobDefaultArgs<ExtArgs extends $Extensions.InternalArgs = $Extensions.DefaultArgs> = {
    /**
     * Select specific fields to fetch from the SyncJob
     */
    select?: SyncJobSelect<ExtArgs> | null
    /**
     * Omit specific fields from the SyncJob
     */
    omit?: SyncJobOmit<ExtArgs> | null
  }


  /**
   * Enums
   */

  export const TransactionIsolationLevel: {
    Serializable: 'Serializable'
  };

  export type TransactionIsolationLevel = (typeof TransactionIsolationLevel)[keyof typeof TransactionIsolationLevel]


  export const AccountScalarFieldEnum: {
    id: 'id',
    userId: 'userId',
    type: 'type',
    provider: 'provider',
    providerAccountId: 'providerAccountId',
    refresh_token: 'refresh_token',
    access_token: 'access_token',
    expires_at: 'expires_at',
    token_type: 'token_type',
    scope: 'scope',
    id_token: 'id_token',
    session_state: 'session_state'
  };

  export type AccountScalarFieldEnum = (typeof AccountScalarFieldEnum)[keyof typeof AccountScalarFieldEnum]


  export const SessionScalarFieldEnum: {
    id: 'id',
    sessionToken: 'sessionToken',
    userId: 'userId',
    expires: 'expires'
  };

  export type SessionScalarFieldEnum = (typeof SessionScalarFieldEnum)[keyof typeof SessionScalarFieldEnum]


  export const UserScalarFieldEnum: {
    id: 'id',
    name: 'name',
    email: 'email',
    emailVerified: 'emailVerified',
    image: 'image'
  };

  export type UserScalarFieldEnum = (typeof UserScalarFieldEnum)[keyof typeof UserScalarFieldEnum]


  export const VerificationTokenScalarFieldEnum: {
    identifier: 'identifier',
    token: 'token',
    expires: 'expires'
  };

  export type VerificationTokenScalarFieldEnum = (typeof VerificationTokenScalarFieldEnum)[keyof typeof VerificationTokenScalarFieldEnum]


  export const EmailVerificationRequestScalarFieldEnum: {
    id: 'id',
    email: 'email',
    createdAt: 'createdAt',
    invalidated: 'invalidated'
  };

  export type EmailVerificationRequestScalarFieldEnum = (typeof EmailVerificationRequestScalarFieldEnum)[keyof typeof EmailVerificationRequestScalarFieldEnum]


  export const LocalUserProfileScalarFieldEnum: {
    id: 'id',
    userId: 'userId',
    publicId: 'publicId',
    email: 'email',
    name: 'name',
    hasCompletedOnboarding: 'hasCompletedOnboarding',
    topics: 'topics',
    topicsDetails: 'topicsDetails',
    regions: 'regions',
    languages: 'languages',
    publications: 'publications',
    lastSyncAt: 'lastSyncAt',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt'
  };

  export type LocalUserProfileScalarFieldEnum = (typeof LocalUserProfileScalarFieldEnum)[keyof typeof LocalUserProfileScalarFieldEnum]


  export const LocalArticleScalarFieldEnum: {
    id: 'id',
    backendId: 'backendId',
    title: 'title',
    visualTitle: 'visualTitle',
    description: 'description',
    content: 'content',
    url: 'url',
    imageUrl: 'imageUrl',
    publishedAt: 'publishedAt',
    readTime: 'readTime',
    isTopHeadline: 'isTopHeadline',
    sourceName: 'sourceName',
    sourceLogoUrl: 'sourceLogoUrl',
    summary: 'summary',
    richContent: 'richContent',
    contentStatus: 'contentStatus',
    contentQuality: 'contentQuality',
    topics: 'topics',
    isRead: 'isRead',
    isSaved: 'isSaved',
    readAt: 'readAt',
    savedAt: 'savedAt',
    lastSyncAt: 'lastSyncAt',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt'
  };

  export type LocalArticleScalarFieldEnum = (typeof LocalArticleScalarFieldEnum)[keyof typeof LocalArticleScalarFieldEnum]


  export const FeedSyncScalarFieldEnum: {
    id: 'id',
    userId: 'userId',
    feedType: 'feedType',
    topicSlug: 'topicSlug',
    lastSyncAt: 'lastSyncAt',
    nextSyncAt: 'nextSyncAt',
    isStale: 'isStale',
    syncInProgress: 'syncInProgress',
    lastPage: 'lastPage',
    hasMore: 'hasMore',
    totalItems: 'totalItems',
    syncCount: 'syncCount',
    lastSyncDuration: 'lastSyncDuration',
    lastError: 'lastError',
    consecutiveErrors: 'consecutiveErrors',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt'
  };

  export type FeedSyncScalarFieldEnum = (typeof FeedSyncScalarFieldEnum)[keyof typeof FeedSyncScalarFieldEnum]


  export const FeedItemScalarFieldEnum: {
    id: 'id',
    feedSyncId: 'feedSyncId',
    articleId: 'articleId',
    position: 'position',
    relevanceScore: 'relevanceScore',
    addedAt: 'addedAt'
  };

  export type FeedItemScalarFieldEnum = (typeof FeedItemScalarFieldEnum)[keyof typeof FeedItemScalarFieldEnum]


  export const SyncJobScalarFieldEnum: {
    id: 'id',
    type: 'type',
    userId: 'userId',
    feedType: 'feedType',
    topicSlug: 'topicSlug',
    articleId: 'articleId',
    status: 'status',
    priority: 'priority',
    attempts: 'attempts',
    maxAttempts: 'maxAttempts',
    scheduledAt: 'scheduledAt',
    startedAt: 'startedAt',
    completedAt: 'completedAt',
    result: 'result',
    error: 'error',
    createdAt: 'createdAt',
    updatedAt: 'updatedAt'
  };

  export type SyncJobScalarFieldEnum = (typeof SyncJobScalarFieldEnum)[keyof typeof SyncJobScalarFieldEnum]


  export const SortOrder: {
    asc: 'asc',
    desc: 'desc'
  };

  export type SortOrder = (typeof SortOrder)[keyof typeof SortOrder]


  export const NullsOrder: {
    first: 'first',
    last: 'last'
  };

  export type NullsOrder = (typeof NullsOrder)[keyof typeof NullsOrder]


  /**
   * Field references
   */


  /**
   * Reference to a field of type 'String'
   */
  export type StringFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'String'>
    


  /**
   * Reference to a field of type 'Int'
   */
  export type IntFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Int'>
    


  /**
   * Reference to a field of type 'DateTime'
   */
  export type DateTimeFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'DateTime'>
    


  /**
   * Reference to a field of type 'Boolean'
   */
  export type BooleanFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Boolean'>
    


  /**
   * Reference to a field of type 'Float'
   */
  export type FloatFieldRefInput<$PrismaModel> = FieldRefInputType<$PrismaModel, 'Float'>
    
  /**
   * Deep Input Types
   */


  export type AccountWhereInput = {
    AND?: AccountWhereInput | AccountWhereInput[]
    OR?: AccountWhereInput[]
    NOT?: AccountWhereInput | AccountWhereInput[]
    id?: StringFilter<"Account"> | string
    userId?: StringFilter<"Account"> | string
    type?: StringFilter<"Account"> | string
    provider?: StringFilter<"Account"> | string
    providerAccountId?: StringFilter<"Account"> | string
    refresh_token?: StringNullableFilter<"Account"> | string | null
    access_token?: StringNullableFilter<"Account"> | string | null
    expires_at?: IntNullableFilter<"Account"> | number | null
    token_type?: StringNullableFilter<"Account"> | string | null
    scope?: StringNullableFilter<"Account"> | string | null
    id_token?: StringNullableFilter<"Account"> | string | null
    session_state?: StringNullableFilter<"Account"> | string | null
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
  }

  export type AccountOrderByWithRelationInput = {
    id?: SortOrder
    userId?: SortOrder
    type?: SortOrder
    provider?: SortOrder
    providerAccountId?: SortOrder
    refresh_token?: SortOrderInput | SortOrder
    access_token?: SortOrderInput | SortOrder
    expires_at?: SortOrderInput | SortOrder
    token_type?: SortOrderInput | SortOrder
    scope?: SortOrderInput | SortOrder
    id_token?: SortOrderInput | SortOrder
    session_state?: SortOrderInput | SortOrder
    user?: UserOrderByWithRelationInput
  }

  export type AccountWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    provider_providerAccountId?: AccountProviderProviderAccountIdCompoundUniqueInput
    AND?: AccountWhereInput | AccountWhereInput[]
    OR?: AccountWhereInput[]
    NOT?: AccountWhereInput | AccountWhereInput[]
    userId?: StringFilter<"Account"> | string
    type?: StringFilter<"Account"> | string
    provider?: StringFilter<"Account"> | string
    providerAccountId?: StringFilter<"Account"> | string
    refresh_token?: StringNullableFilter<"Account"> | string | null
    access_token?: StringNullableFilter<"Account"> | string | null
    expires_at?: IntNullableFilter<"Account"> | number | null
    token_type?: StringNullableFilter<"Account"> | string | null
    scope?: StringNullableFilter<"Account"> | string | null
    id_token?: StringNullableFilter<"Account"> | string | null
    session_state?: StringNullableFilter<"Account"> | string | null
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
  }, "id" | "provider_providerAccountId">

  export type AccountOrderByWithAggregationInput = {
    id?: SortOrder
    userId?: SortOrder
    type?: SortOrder
    provider?: SortOrder
    providerAccountId?: SortOrder
    refresh_token?: SortOrderInput | SortOrder
    access_token?: SortOrderInput | SortOrder
    expires_at?: SortOrderInput | SortOrder
    token_type?: SortOrderInput | SortOrder
    scope?: SortOrderInput | SortOrder
    id_token?: SortOrderInput | SortOrder
    session_state?: SortOrderInput | SortOrder
    _count?: AccountCountOrderByAggregateInput
    _avg?: AccountAvgOrderByAggregateInput
    _max?: AccountMaxOrderByAggregateInput
    _min?: AccountMinOrderByAggregateInput
    _sum?: AccountSumOrderByAggregateInput
  }

  export type AccountScalarWhereWithAggregatesInput = {
    AND?: AccountScalarWhereWithAggregatesInput | AccountScalarWhereWithAggregatesInput[]
    OR?: AccountScalarWhereWithAggregatesInput[]
    NOT?: AccountScalarWhereWithAggregatesInput | AccountScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"Account"> | string
    userId?: StringWithAggregatesFilter<"Account"> | string
    type?: StringWithAggregatesFilter<"Account"> | string
    provider?: StringWithAggregatesFilter<"Account"> | string
    providerAccountId?: StringWithAggregatesFilter<"Account"> | string
    refresh_token?: StringNullableWithAggregatesFilter<"Account"> | string | null
    access_token?: StringNullableWithAggregatesFilter<"Account"> | string | null
    expires_at?: IntNullableWithAggregatesFilter<"Account"> | number | null
    token_type?: StringNullableWithAggregatesFilter<"Account"> | string | null
    scope?: StringNullableWithAggregatesFilter<"Account"> | string | null
    id_token?: StringNullableWithAggregatesFilter<"Account"> | string | null
    session_state?: StringNullableWithAggregatesFilter<"Account"> | string | null
  }

  export type SessionWhereInput = {
    AND?: SessionWhereInput | SessionWhereInput[]
    OR?: SessionWhereInput[]
    NOT?: SessionWhereInput | SessionWhereInput[]
    id?: StringFilter<"Session"> | string
    sessionToken?: StringFilter<"Session"> | string
    userId?: StringFilter<"Session"> | string
    expires?: DateTimeFilter<"Session"> | Date | string
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
  }

  export type SessionOrderByWithRelationInput = {
    id?: SortOrder
    sessionToken?: SortOrder
    userId?: SortOrder
    expires?: SortOrder
    user?: UserOrderByWithRelationInput
  }

  export type SessionWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    sessionToken?: string
    AND?: SessionWhereInput | SessionWhereInput[]
    OR?: SessionWhereInput[]
    NOT?: SessionWhereInput | SessionWhereInput[]
    userId?: StringFilter<"Session"> | string
    expires?: DateTimeFilter<"Session"> | Date | string
    user?: XOR<UserScalarRelationFilter, UserWhereInput>
  }, "id" | "sessionToken">

  export type SessionOrderByWithAggregationInput = {
    id?: SortOrder
    sessionToken?: SortOrder
    userId?: SortOrder
    expires?: SortOrder
    _count?: SessionCountOrderByAggregateInput
    _max?: SessionMaxOrderByAggregateInput
    _min?: SessionMinOrderByAggregateInput
  }

  export type SessionScalarWhereWithAggregatesInput = {
    AND?: SessionScalarWhereWithAggregatesInput | SessionScalarWhereWithAggregatesInput[]
    OR?: SessionScalarWhereWithAggregatesInput[]
    NOT?: SessionScalarWhereWithAggregatesInput | SessionScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"Session"> | string
    sessionToken?: StringWithAggregatesFilter<"Session"> | string
    userId?: StringWithAggregatesFilter<"Session"> | string
    expires?: DateTimeWithAggregatesFilter<"Session"> | Date | string
  }

  export type UserWhereInput = {
    AND?: UserWhereInput | UserWhereInput[]
    OR?: UserWhereInput[]
    NOT?: UserWhereInput | UserWhereInput[]
    id?: StringFilter<"User"> | string
    name?: StringNullableFilter<"User"> | string | null
    email?: StringNullableFilter<"User"> | string | null
    emailVerified?: DateTimeNullableFilter<"User"> | Date | string | null
    image?: StringNullableFilter<"User"> | string | null
    accounts?: AccountListRelationFilter
    sessions?: SessionListRelationFilter
  }

  export type UserOrderByWithRelationInput = {
    id?: SortOrder
    name?: SortOrderInput | SortOrder
    email?: SortOrderInput | SortOrder
    emailVerified?: SortOrderInput | SortOrder
    image?: SortOrderInput | SortOrder
    accounts?: AccountOrderByRelationAggregateInput
    sessions?: SessionOrderByRelationAggregateInput
  }

  export type UserWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    email?: string
    AND?: UserWhereInput | UserWhereInput[]
    OR?: UserWhereInput[]
    NOT?: UserWhereInput | UserWhereInput[]
    name?: StringNullableFilter<"User"> | string | null
    emailVerified?: DateTimeNullableFilter<"User"> | Date | string | null
    image?: StringNullableFilter<"User"> | string | null
    accounts?: AccountListRelationFilter
    sessions?: SessionListRelationFilter
  }, "id" | "email">

  export type UserOrderByWithAggregationInput = {
    id?: SortOrder
    name?: SortOrderInput | SortOrder
    email?: SortOrderInput | SortOrder
    emailVerified?: SortOrderInput | SortOrder
    image?: SortOrderInput | SortOrder
    _count?: UserCountOrderByAggregateInput
    _max?: UserMaxOrderByAggregateInput
    _min?: UserMinOrderByAggregateInput
  }

  export type UserScalarWhereWithAggregatesInput = {
    AND?: UserScalarWhereWithAggregatesInput | UserScalarWhereWithAggregatesInput[]
    OR?: UserScalarWhereWithAggregatesInput[]
    NOT?: UserScalarWhereWithAggregatesInput | UserScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"User"> | string
    name?: StringNullableWithAggregatesFilter<"User"> | string | null
    email?: StringNullableWithAggregatesFilter<"User"> | string | null
    emailVerified?: DateTimeNullableWithAggregatesFilter<"User"> | Date | string | null
    image?: StringNullableWithAggregatesFilter<"User"> | string | null
  }

  export type VerificationTokenWhereInput = {
    AND?: VerificationTokenWhereInput | VerificationTokenWhereInput[]
    OR?: VerificationTokenWhereInput[]
    NOT?: VerificationTokenWhereInput | VerificationTokenWhereInput[]
    identifier?: StringFilter<"VerificationToken"> | string
    token?: StringFilter<"VerificationToken"> | string
    expires?: DateTimeFilter<"VerificationToken"> | Date | string
  }

  export type VerificationTokenOrderByWithRelationInput = {
    identifier?: SortOrder
    token?: SortOrder
    expires?: SortOrder
  }

  export type VerificationTokenWhereUniqueInput = Prisma.AtLeast<{
    token?: string
    identifier_token?: VerificationTokenIdentifierTokenCompoundUniqueInput
    AND?: VerificationTokenWhereInput | VerificationTokenWhereInput[]
    OR?: VerificationTokenWhereInput[]
    NOT?: VerificationTokenWhereInput | VerificationTokenWhereInput[]
    identifier?: StringFilter<"VerificationToken"> | string
    expires?: DateTimeFilter<"VerificationToken"> | Date | string
  }, "token" | "identifier_token">

  export type VerificationTokenOrderByWithAggregationInput = {
    identifier?: SortOrder
    token?: SortOrder
    expires?: SortOrder
    _count?: VerificationTokenCountOrderByAggregateInput
    _max?: VerificationTokenMaxOrderByAggregateInput
    _min?: VerificationTokenMinOrderByAggregateInput
  }

  export type VerificationTokenScalarWhereWithAggregatesInput = {
    AND?: VerificationTokenScalarWhereWithAggregatesInput | VerificationTokenScalarWhereWithAggregatesInput[]
    OR?: VerificationTokenScalarWhereWithAggregatesInput[]
    NOT?: VerificationTokenScalarWhereWithAggregatesInput | VerificationTokenScalarWhereWithAggregatesInput[]
    identifier?: StringWithAggregatesFilter<"VerificationToken"> | string
    token?: StringWithAggregatesFilter<"VerificationToken"> | string
    expires?: DateTimeWithAggregatesFilter<"VerificationToken"> | Date | string
  }

  export type EmailVerificationRequestWhereInput = {
    AND?: EmailVerificationRequestWhereInput | EmailVerificationRequestWhereInput[]
    OR?: EmailVerificationRequestWhereInput[]
    NOT?: EmailVerificationRequestWhereInput | EmailVerificationRequestWhereInput[]
    id?: StringFilter<"EmailVerificationRequest"> | string
    email?: StringFilter<"EmailVerificationRequest"> | string
    createdAt?: DateTimeFilter<"EmailVerificationRequest"> | Date | string
    invalidated?: BoolFilter<"EmailVerificationRequest"> | boolean
  }

  export type EmailVerificationRequestOrderByWithRelationInput = {
    id?: SortOrder
    email?: SortOrder
    createdAt?: SortOrder
    invalidated?: SortOrder
  }

  export type EmailVerificationRequestWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    AND?: EmailVerificationRequestWhereInput | EmailVerificationRequestWhereInput[]
    OR?: EmailVerificationRequestWhereInput[]
    NOT?: EmailVerificationRequestWhereInput | EmailVerificationRequestWhereInput[]
    email?: StringFilter<"EmailVerificationRequest"> | string
    createdAt?: DateTimeFilter<"EmailVerificationRequest"> | Date | string
    invalidated?: BoolFilter<"EmailVerificationRequest"> | boolean
  }, "id">

  export type EmailVerificationRequestOrderByWithAggregationInput = {
    id?: SortOrder
    email?: SortOrder
    createdAt?: SortOrder
    invalidated?: SortOrder
    _count?: EmailVerificationRequestCountOrderByAggregateInput
    _max?: EmailVerificationRequestMaxOrderByAggregateInput
    _min?: EmailVerificationRequestMinOrderByAggregateInput
  }

  export type EmailVerificationRequestScalarWhereWithAggregatesInput = {
    AND?: EmailVerificationRequestScalarWhereWithAggregatesInput | EmailVerificationRequestScalarWhereWithAggregatesInput[]
    OR?: EmailVerificationRequestScalarWhereWithAggregatesInput[]
    NOT?: EmailVerificationRequestScalarWhereWithAggregatesInput | EmailVerificationRequestScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"EmailVerificationRequest"> | string
    email?: StringWithAggregatesFilter<"EmailVerificationRequest"> | string
    createdAt?: DateTimeWithAggregatesFilter<"EmailVerificationRequest"> | Date | string
    invalidated?: BoolWithAggregatesFilter<"EmailVerificationRequest"> | boolean
  }

  export type LocalUserProfileWhereInput = {
    AND?: LocalUserProfileWhereInput | LocalUserProfileWhereInput[]
    OR?: LocalUserProfileWhereInput[]
    NOT?: LocalUserProfileWhereInput | LocalUserProfileWhereInput[]
    id?: StringFilter<"LocalUserProfile"> | string
    userId?: StringFilter<"LocalUserProfile"> | string
    publicId?: StringFilter<"LocalUserProfile"> | string
    email?: StringFilter<"LocalUserProfile"> | string
    name?: StringFilter<"LocalUserProfile"> | string
    hasCompletedOnboarding?: BoolFilter<"LocalUserProfile"> | boolean
    topics?: StringFilter<"LocalUserProfile"> | string
    topicsDetails?: StringNullableFilter<"LocalUserProfile"> | string | null
    regions?: StringFilter<"LocalUserProfile"> | string
    languages?: StringFilter<"LocalUserProfile"> | string
    publications?: StringFilter<"LocalUserProfile"> | string
    lastSyncAt?: DateTimeFilter<"LocalUserProfile"> | Date | string
    createdAt?: DateTimeFilter<"LocalUserProfile"> | Date | string
    updatedAt?: DateTimeFilter<"LocalUserProfile"> | Date | string
    feedSyncs?: FeedSyncListRelationFilter
  }

  export type LocalUserProfileOrderByWithRelationInput = {
    id?: SortOrder
    userId?: SortOrder
    publicId?: SortOrder
    email?: SortOrder
    name?: SortOrder
    hasCompletedOnboarding?: SortOrder
    topics?: SortOrder
    topicsDetails?: SortOrderInput | SortOrder
    regions?: SortOrder
    languages?: SortOrder
    publications?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    feedSyncs?: FeedSyncOrderByRelationAggregateInput
  }

  export type LocalUserProfileWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    userId?: string
    publicId?: string
    AND?: LocalUserProfileWhereInput | LocalUserProfileWhereInput[]
    OR?: LocalUserProfileWhereInput[]
    NOT?: LocalUserProfileWhereInput | LocalUserProfileWhereInput[]
    email?: StringFilter<"LocalUserProfile"> | string
    name?: StringFilter<"LocalUserProfile"> | string
    hasCompletedOnboarding?: BoolFilter<"LocalUserProfile"> | boolean
    topics?: StringFilter<"LocalUserProfile"> | string
    topicsDetails?: StringNullableFilter<"LocalUserProfile"> | string | null
    regions?: StringFilter<"LocalUserProfile"> | string
    languages?: StringFilter<"LocalUserProfile"> | string
    publications?: StringFilter<"LocalUserProfile"> | string
    lastSyncAt?: DateTimeFilter<"LocalUserProfile"> | Date | string
    createdAt?: DateTimeFilter<"LocalUserProfile"> | Date | string
    updatedAt?: DateTimeFilter<"LocalUserProfile"> | Date | string
    feedSyncs?: FeedSyncListRelationFilter
  }, "id" | "userId" | "publicId">

  export type LocalUserProfileOrderByWithAggregationInput = {
    id?: SortOrder
    userId?: SortOrder
    publicId?: SortOrder
    email?: SortOrder
    name?: SortOrder
    hasCompletedOnboarding?: SortOrder
    topics?: SortOrder
    topicsDetails?: SortOrderInput | SortOrder
    regions?: SortOrder
    languages?: SortOrder
    publications?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    _count?: LocalUserProfileCountOrderByAggregateInput
    _max?: LocalUserProfileMaxOrderByAggregateInput
    _min?: LocalUserProfileMinOrderByAggregateInput
  }

  export type LocalUserProfileScalarWhereWithAggregatesInput = {
    AND?: LocalUserProfileScalarWhereWithAggregatesInput | LocalUserProfileScalarWhereWithAggregatesInput[]
    OR?: LocalUserProfileScalarWhereWithAggregatesInput[]
    NOT?: LocalUserProfileScalarWhereWithAggregatesInput | LocalUserProfileScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    userId?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    publicId?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    email?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    name?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    hasCompletedOnboarding?: BoolWithAggregatesFilter<"LocalUserProfile"> | boolean
    topics?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    topicsDetails?: StringNullableWithAggregatesFilter<"LocalUserProfile"> | string | null
    regions?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    languages?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    publications?: StringWithAggregatesFilter<"LocalUserProfile"> | string
    lastSyncAt?: DateTimeWithAggregatesFilter<"LocalUserProfile"> | Date | string
    createdAt?: DateTimeWithAggregatesFilter<"LocalUserProfile"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"LocalUserProfile"> | Date | string
  }

  export type LocalArticleWhereInput = {
    AND?: LocalArticleWhereInput | LocalArticleWhereInput[]
    OR?: LocalArticleWhereInput[]
    NOT?: LocalArticleWhereInput | LocalArticleWhereInput[]
    id?: StringFilter<"LocalArticle"> | string
    backendId?: StringFilter<"LocalArticle"> | string
    title?: StringFilter<"LocalArticle"> | string
    visualTitle?: StringNullableFilter<"LocalArticle"> | string | null
    description?: StringFilter<"LocalArticle"> | string
    content?: StringNullableFilter<"LocalArticle"> | string | null
    url?: StringFilter<"LocalArticle"> | string
    imageUrl?: StringNullableFilter<"LocalArticle"> | string | null
    publishedAt?: DateTimeFilter<"LocalArticle"> | Date | string
    readTime?: IntNullableFilter<"LocalArticle"> | number | null
    isTopHeadline?: BoolFilter<"LocalArticle"> | boolean
    sourceName?: StringFilter<"LocalArticle"> | string
    sourceLogoUrl?: StringNullableFilter<"LocalArticle"> | string | null
    summary?: StringNullableFilter<"LocalArticle"> | string | null
    richContent?: StringNullableFilter<"LocalArticle"> | string | null
    contentStatus?: StringNullableFilter<"LocalArticle"> | string | null
    contentQuality?: StringNullableFilter<"LocalArticle"> | string | null
    topics?: StringNullableFilter<"LocalArticle"> | string | null
    isRead?: BoolFilter<"LocalArticle"> | boolean
    isSaved?: BoolFilter<"LocalArticle"> | boolean
    readAt?: DateTimeNullableFilter<"LocalArticle"> | Date | string | null
    savedAt?: DateTimeNullableFilter<"LocalArticle"> | Date | string | null
    lastSyncAt?: DateTimeFilter<"LocalArticle"> | Date | string
    createdAt?: DateTimeFilter<"LocalArticle"> | Date | string
    updatedAt?: DateTimeFilter<"LocalArticle"> | Date | string
    feedItems?: FeedItemListRelationFilter
  }

  export type LocalArticleOrderByWithRelationInput = {
    id?: SortOrder
    backendId?: SortOrder
    title?: SortOrder
    visualTitle?: SortOrderInput | SortOrder
    description?: SortOrder
    content?: SortOrderInput | SortOrder
    url?: SortOrder
    imageUrl?: SortOrderInput | SortOrder
    publishedAt?: SortOrder
    readTime?: SortOrderInput | SortOrder
    isTopHeadline?: SortOrder
    sourceName?: SortOrder
    sourceLogoUrl?: SortOrderInput | SortOrder
    summary?: SortOrderInput | SortOrder
    richContent?: SortOrderInput | SortOrder
    contentStatus?: SortOrderInput | SortOrder
    contentQuality?: SortOrderInput | SortOrder
    topics?: SortOrderInput | SortOrder
    isRead?: SortOrder
    isSaved?: SortOrder
    readAt?: SortOrderInput | SortOrder
    savedAt?: SortOrderInput | SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    feedItems?: FeedItemOrderByRelationAggregateInput
  }

  export type LocalArticleWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    backendId?: string
    AND?: LocalArticleWhereInput | LocalArticleWhereInput[]
    OR?: LocalArticleWhereInput[]
    NOT?: LocalArticleWhereInput | LocalArticleWhereInput[]
    title?: StringFilter<"LocalArticle"> | string
    visualTitle?: StringNullableFilter<"LocalArticle"> | string | null
    description?: StringFilter<"LocalArticle"> | string
    content?: StringNullableFilter<"LocalArticle"> | string | null
    url?: StringFilter<"LocalArticle"> | string
    imageUrl?: StringNullableFilter<"LocalArticle"> | string | null
    publishedAt?: DateTimeFilter<"LocalArticle"> | Date | string
    readTime?: IntNullableFilter<"LocalArticle"> | number | null
    isTopHeadline?: BoolFilter<"LocalArticle"> | boolean
    sourceName?: StringFilter<"LocalArticle"> | string
    sourceLogoUrl?: StringNullableFilter<"LocalArticle"> | string | null
    summary?: StringNullableFilter<"LocalArticle"> | string | null
    richContent?: StringNullableFilter<"LocalArticle"> | string | null
    contentStatus?: StringNullableFilter<"LocalArticle"> | string | null
    contentQuality?: StringNullableFilter<"LocalArticle"> | string | null
    topics?: StringNullableFilter<"LocalArticle"> | string | null
    isRead?: BoolFilter<"LocalArticle"> | boolean
    isSaved?: BoolFilter<"LocalArticle"> | boolean
    readAt?: DateTimeNullableFilter<"LocalArticle"> | Date | string | null
    savedAt?: DateTimeNullableFilter<"LocalArticle"> | Date | string | null
    lastSyncAt?: DateTimeFilter<"LocalArticle"> | Date | string
    createdAt?: DateTimeFilter<"LocalArticle"> | Date | string
    updatedAt?: DateTimeFilter<"LocalArticle"> | Date | string
    feedItems?: FeedItemListRelationFilter
  }, "id" | "backendId">

  export type LocalArticleOrderByWithAggregationInput = {
    id?: SortOrder
    backendId?: SortOrder
    title?: SortOrder
    visualTitle?: SortOrderInput | SortOrder
    description?: SortOrder
    content?: SortOrderInput | SortOrder
    url?: SortOrder
    imageUrl?: SortOrderInput | SortOrder
    publishedAt?: SortOrder
    readTime?: SortOrderInput | SortOrder
    isTopHeadline?: SortOrder
    sourceName?: SortOrder
    sourceLogoUrl?: SortOrderInput | SortOrder
    summary?: SortOrderInput | SortOrder
    richContent?: SortOrderInput | SortOrder
    contentStatus?: SortOrderInput | SortOrder
    contentQuality?: SortOrderInput | SortOrder
    topics?: SortOrderInput | SortOrder
    isRead?: SortOrder
    isSaved?: SortOrder
    readAt?: SortOrderInput | SortOrder
    savedAt?: SortOrderInput | SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    _count?: LocalArticleCountOrderByAggregateInput
    _avg?: LocalArticleAvgOrderByAggregateInput
    _max?: LocalArticleMaxOrderByAggregateInput
    _min?: LocalArticleMinOrderByAggregateInput
    _sum?: LocalArticleSumOrderByAggregateInput
  }

  export type LocalArticleScalarWhereWithAggregatesInput = {
    AND?: LocalArticleScalarWhereWithAggregatesInput | LocalArticleScalarWhereWithAggregatesInput[]
    OR?: LocalArticleScalarWhereWithAggregatesInput[]
    NOT?: LocalArticleScalarWhereWithAggregatesInput | LocalArticleScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"LocalArticle"> | string
    backendId?: StringWithAggregatesFilter<"LocalArticle"> | string
    title?: StringWithAggregatesFilter<"LocalArticle"> | string
    visualTitle?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    description?: StringWithAggregatesFilter<"LocalArticle"> | string
    content?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    url?: StringWithAggregatesFilter<"LocalArticle"> | string
    imageUrl?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    publishedAt?: DateTimeWithAggregatesFilter<"LocalArticle"> | Date | string
    readTime?: IntNullableWithAggregatesFilter<"LocalArticle"> | number | null
    isTopHeadline?: BoolWithAggregatesFilter<"LocalArticle"> | boolean
    sourceName?: StringWithAggregatesFilter<"LocalArticle"> | string
    sourceLogoUrl?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    summary?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    richContent?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    contentStatus?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    contentQuality?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    topics?: StringNullableWithAggregatesFilter<"LocalArticle"> | string | null
    isRead?: BoolWithAggregatesFilter<"LocalArticle"> | boolean
    isSaved?: BoolWithAggregatesFilter<"LocalArticle"> | boolean
    readAt?: DateTimeNullableWithAggregatesFilter<"LocalArticle"> | Date | string | null
    savedAt?: DateTimeNullableWithAggregatesFilter<"LocalArticle"> | Date | string | null
    lastSyncAt?: DateTimeWithAggregatesFilter<"LocalArticle"> | Date | string
    createdAt?: DateTimeWithAggregatesFilter<"LocalArticle"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"LocalArticle"> | Date | string
  }

  export type FeedSyncWhereInput = {
    AND?: FeedSyncWhereInput | FeedSyncWhereInput[]
    OR?: FeedSyncWhereInput[]
    NOT?: FeedSyncWhereInput | FeedSyncWhereInput[]
    id?: StringFilter<"FeedSync"> | string
    userId?: StringFilter<"FeedSync"> | string
    feedType?: StringFilter<"FeedSync"> | string
    topicSlug?: StringNullableFilter<"FeedSync"> | string | null
    lastSyncAt?: DateTimeFilter<"FeedSync"> | Date | string
    nextSyncAt?: DateTimeNullableFilter<"FeedSync"> | Date | string | null
    isStale?: BoolFilter<"FeedSync"> | boolean
    syncInProgress?: BoolFilter<"FeedSync"> | boolean
    lastPage?: IntFilter<"FeedSync"> | number
    hasMore?: BoolFilter<"FeedSync"> | boolean
    totalItems?: IntNullableFilter<"FeedSync"> | number | null
    syncCount?: IntFilter<"FeedSync"> | number
    lastSyncDuration?: IntNullableFilter<"FeedSync"> | number | null
    lastError?: StringNullableFilter<"FeedSync"> | string | null
    consecutiveErrors?: IntFilter<"FeedSync"> | number
    createdAt?: DateTimeFilter<"FeedSync"> | Date | string
    updatedAt?: DateTimeFilter<"FeedSync"> | Date | string
    userProfile?: XOR<LocalUserProfileScalarRelationFilter, LocalUserProfileWhereInput>
    feedItems?: FeedItemListRelationFilter
  }

  export type FeedSyncOrderByWithRelationInput = {
    id?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrderInput | SortOrder
    lastSyncAt?: SortOrder
    nextSyncAt?: SortOrderInput | SortOrder
    isStale?: SortOrder
    syncInProgress?: SortOrder
    lastPage?: SortOrder
    hasMore?: SortOrder
    totalItems?: SortOrderInput | SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrderInput | SortOrder
    lastError?: SortOrderInput | SortOrder
    consecutiveErrors?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    userProfile?: LocalUserProfileOrderByWithRelationInput
    feedItems?: FeedItemOrderByRelationAggregateInput
  }

  export type FeedSyncWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    userId_feedType_topicSlug?: FeedSyncUserIdFeedTypeTopicSlugCompoundUniqueInput
    AND?: FeedSyncWhereInput | FeedSyncWhereInput[]
    OR?: FeedSyncWhereInput[]
    NOT?: FeedSyncWhereInput | FeedSyncWhereInput[]
    userId?: StringFilter<"FeedSync"> | string
    feedType?: StringFilter<"FeedSync"> | string
    topicSlug?: StringNullableFilter<"FeedSync"> | string | null
    lastSyncAt?: DateTimeFilter<"FeedSync"> | Date | string
    nextSyncAt?: DateTimeNullableFilter<"FeedSync"> | Date | string | null
    isStale?: BoolFilter<"FeedSync"> | boolean
    syncInProgress?: BoolFilter<"FeedSync"> | boolean
    lastPage?: IntFilter<"FeedSync"> | number
    hasMore?: BoolFilter<"FeedSync"> | boolean
    totalItems?: IntNullableFilter<"FeedSync"> | number | null
    syncCount?: IntFilter<"FeedSync"> | number
    lastSyncDuration?: IntNullableFilter<"FeedSync"> | number | null
    lastError?: StringNullableFilter<"FeedSync"> | string | null
    consecutiveErrors?: IntFilter<"FeedSync"> | number
    createdAt?: DateTimeFilter<"FeedSync"> | Date | string
    updatedAt?: DateTimeFilter<"FeedSync"> | Date | string
    userProfile?: XOR<LocalUserProfileScalarRelationFilter, LocalUserProfileWhereInput>
    feedItems?: FeedItemListRelationFilter
  }, "id" | "userId_feedType_topicSlug">

  export type FeedSyncOrderByWithAggregationInput = {
    id?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrderInput | SortOrder
    lastSyncAt?: SortOrder
    nextSyncAt?: SortOrderInput | SortOrder
    isStale?: SortOrder
    syncInProgress?: SortOrder
    lastPage?: SortOrder
    hasMore?: SortOrder
    totalItems?: SortOrderInput | SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrderInput | SortOrder
    lastError?: SortOrderInput | SortOrder
    consecutiveErrors?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    _count?: FeedSyncCountOrderByAggregateInput
    _avg?: FeedSyncAvgOrderByAggregateInput
    _max?: FeedSyncMaxOrderByAggregateInput
    _min?: FeedSyncMinOrderByAggregateInput
    _sum?: FeedSyncSumOrderByAggregateInput
  }

  export type FeedSyncScalarWhereWithAggregatesInput = {
    AND?: FeedSyncScalarWhereWithAggregatesInput | FeedSyncScalarWhereWithAggregatesInput[]
    OR?: FeedSyncScalarWhereWithAggregatesInput[]
    NOT?: FeedSyncScalarWhereWithAggregatesInput | FeedSyncScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"FeedSync"> | string
    userId?: StringWithAggregatesFilter<"FeedSync"> | string
    feedType?: StringWithAggregatesFilter<"FeedSync"> | string
    topicSlug?: StringNullableWithAggregatesFilter<"FeedSync"> | string | null
    lastSyncAt?: DateTimeWithAggregatesFilter<"FeedSync"> | Date | string
    nextSyncAt?: DateTimeNullableWithAggregatesFilter<"FeedSync"> | Date | string | null
    isStale?: BoolWithAggregatesFilter<"FeedSync"> | boolean
    syncInProgress?: BoolWithAggregatesFilter<"FeedSync"> | boolean
    lastPage?: IntWithAggregatesFilter<"FeedSync"> | number
    hasMore?: BoolWithAggregatesFilter<"FeedSync"> | boolean
    totalItems?: IntNullableWithAggregatesFilter<"FeedSync"> | number | null
    syncCount?: IntWithAggregatesFilter<"FeedSync"> | number
    lastSyncDuration?: IntNullableWithAggregatesFilter<"FeedSync"> | number | null
    lastError?: StringNullableWithAggregatesFilter<"FeedSync"> | string | null
    consecutiveErrors?: IntWithAggregatesFilter<"FeedSync"> | number
    createdAt?: DateTimeWithAggregatesFilter<"FeedSync"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"FeedSync"> | Date | string
  }

  export type FeedItemWhereInput = {
    AND?: FeedItemWhereInput | FeedItemWhereInput[]
    OR?: FeedItemWhereInput[]
    NOT?: FeedItemWhereInput | FeedItemWhereInput[]
    id?: StringFilter<"FeedItem"> | string
    feedSyncId?: StringFilter<"FeedItem"> | string
    articleId?: StringFilter<"FeedItem"> | string
    position?: IntFilter<"FeedItem"> | number
    relevanceScore?: FloatNullableFilter<"FeedItem"> | number | null
    addedAt?: DateTimeFilter<"FeedItem"> | Date | string
    feedSync?: XOR<FeedSyncScalarRelationFilter, FeedSyncWhereInput>
    article?: XOR<LocalArticleScalarRelationFilter, LocalArticleWhereInput>
  }

  export type FeedItemOrderByWithRelationInput = {
    id?: SortOrder
    feedSyncId?: SortOrder
    articleId?: SortOrder
    position?: SortOrder
    relevanceScore?: SortOrderInput | SortOrder
    addedAt?: SortOrder
    feedSync?: FeedSyncOrderByWithRelationInput
    article?: LocalArticleOrderByWithRelationInput
  }

  export type FeedItemWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    feedSyncId_articleId?: FeedItemFeedSyncIdArticleIdCompoundUniqueInput
    AND?: FeedItemWhereInput | FeedItemWhereInput[]
    OR?: FeedItemWhereInput[]
    NOT?: FeedItemWhereInput | FeedItemWhereInput[]
    feedSyncId?: StringFilter<"FeedItem"> | string
    articleId?: StringFilter<"FeedItem"> | string
    position?: IntFilter<"FeedItem"> | number
    relevanceScore?: FloatNullableFilter<"FeedItem"> | number | null
    addedAt?: DateTimeFilter<"FeedItem"> | Date | string
    feedSync?: XOR<FeedSyncScalarRelationFilter, FeedSyncWhereInput>
    article?: XOR<LocalArticleScalarRelationFilter, LocalArticleWhereInput>
  }, "id" | "feedSyncId_articleId">

  export type FeedItemOrderByWithAggregationInput = {
    id?: SortOrder
    feedSyncId?: SortOrder
    articleId?: SortOrder
    position?: SortOrder
    relevanceScore?: SortOrderInput | SortOrder
    addedAt?: SortOrder
    _count?: FeedItemCountOrderByAggregateInput
    _avg?: FeedItemAvgOrderByAggregateInput
    _max?: FeedItemMaxOrderByAggregateInput
    _min?: FeedItemMinOrderByAggregateInput
    _sum?: FeedItemSumOrderByAggregateInput
  }

  export type FeedItemScalarWhereWithAggregatesInput = {
    AND?: FeedItemScalarWhereWithAggregatesInput | FeedItemScalarWhereWithAggregatesInput[]
    OR?: FeedItemScalarWhereWithAggregatesInput[]
    NOT?: FeedItemScalarWhereWithAggregatesInput | FeedItemScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"FeedItem"> | string
    feedSyncId?: StringWithAggregatesFilter<"FeedItem"> | string
    articleId?: StringWithAggregatesFilter<"FeedItem"> | string
    position?: IntWithAggregatesFilter<"FeedItem"> | number
    relevanceScore?: FloatNullableWithAggregatesFilter<"FeedItem"> | number | null
    addedAt?: DateTimeWithAggregatesFilter<"FeedItem"> | Date | string
  }

  export type SyncJobWhereInput = {
    AND?: SyncJobWhereInput | SyncJobWhereInput[]
    OR?: SyncJobWhereInput[]
    NOT?: SyncJobWhereInput | SyncJobWhereInput[]
    id?: StringFilter<"SyncJob"> | string
    type?: StringFilter<"SyncJob"> | string
    userId?: StringNullableFilter<"SyncJob"> | string | null
    feedType?: StringNullableFilter<"SyncJob"> | string | null
    topicSlug?: StringNullableFilter<"SyncJob"> | string | null
    articleId?: StringNullableFilter<"SyncJob"> | string | null
    status?: StringFilter<"SyncJob"> | string
    priority?: IntFilter<"SyncJob"> | number
    attempts?: IntFilter<"SyncJob"> | number
    maxAttempts?: IntFilter<"SyncJob"> | number
    scheduledAt?: DateTimeFilter<"SyncJob"> | Date | string
    startedAt?: DateTimeNullableFilter<"SyncJob"> | Date | string | null
    completedAt?: DateTimeNullableFilter<"SyncJob"> | Date | string | null
    result?: StringNullableFilter<"SyncJob"> | string | null
    error?: StringNullableFilter<"SyncJob"> | string | null
    createdAt?: DateTimeFilter<"SyncJob"> | Date | string
    updatedAt?: DateTimeFilter<"SyncJob"> | Date | string
  }

  export type SyncJobOrderByWithRelationInput = {
    id?: SortOrder
    type?: SortOrder
    userId?: SortOrderInput | SortOrder
    feedType?: SortOrderInput | SortOrder
    topicSlug?: SortOrderInput | SortOrder
    articleId?: SortOrderInput | SortOrder
    status?: SortOrder
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
    scheduledAt?: SortOrder
    startedAt?: SortOrderInput | SortOrder
    completedAt?: SortOrderInput | SortOrder
    result?: SortOrderInput | SortOrder
    error?: SortOrderInput | SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type SyncJobWhereUniqueInput = Prisma.AtLeast<{
    id?: string
    AND?: SyncJobWhereInput | SyncJobWhereInput[]
    OR?: SyncJobWhereInput[]
    NOT?: SyncJobWhereInput | SyncJobWhereInput[]
    type?: StringFilter<"SyncJob"> | string
    userId?: StringNullableFilter<"SyncJob"> | string | null
    feedType?: StringNullableFilter<"SyncJob"> | string | null
    topicSlug?: StringNullableFilter<"SyncJob"> | string | null
    articleId?: StringNullableFilter<"SyncJob"> | string | null
    status?: StringFilter<"SyncJob"> | string
    priority?: IntFilter<"SyncJob"> | number
    attempts?: IntFilter<"SyncJob"> | number
    maxAttempts?: IntFilter<"SyncJob"> | number
    scheduledAt?: DateTimeFilter<"SyncJob"> | Date | string
    startedAt?: DateTimeNullableFilter<"SyncJob"> | Date | string | null
    completedAt?: DateTimeNullableFilter<"SyncJob"> | Date | string | null
    result?: StringNullableFilter<"SyncJob"> | string | null
    error?: StringNullableFilter<"SyncJob"> | string | null
    createdAt?: DateTimeFilter<"SyncJob"> | Date | string
    updatedAt?: DateTimeFilter<"SyncJob"> | Date | string
  }, "id">

  export type SyncJobOrderByWithAggregationInput = {
    id?: SortOrder
    type?: SortOrder
    userId?: SortOrderInput | SortOrder
    feedType?: SortOrderInput | SortOrder
    topicSlug?: SortOrderInput | SortOrder
    articleId?: SortOrderInput | SortOrder
    status?: SortOrder
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
    scheduledAt?: SortOrder
    startedAt?: SortOrderInput | SortOrder
    completedAt?: SortOrderInput | SortOrder
    result?: SortOrderInput | SortOrder
    error?: SortOrderInput | SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
    _count?: SyncJobCountOrderByAggregateInput
    _avg?: SyncJobAvgOrderByAggregateInput
    _max?: SyncJobMaxOrderByAggregateInput
    _min?: SyncJobMinOrderByAggregateInput
    _sum?: SyncJobSumOrderByAggregateInput
  }

  export type SyncJobScalarWhereWithAggregatesInput = {
    AND?: SyncJobScalarWhereWithAggregatesInput | SyncJobScalarWhereWithAggregatesInput[]
    OR?: SyncJobScalarWhereWithAggregatesInput[]
    NOT?: SyncJobScalarWhereWithAggregatesInput | SyncJobScalarWhereWithAggregatesInput[]
    id?: StringWithAggregatesFilter<"SyncJob"> | string
    type?: StringWithAggregatesFilter<"SyncJob"> | string
    userId?: StringNullableWithAggregatesFilter<"SyncJob"> | string | null
    feedType?: StringNullableWithAggregatesFilter<"SyncJob"> | string | null
    topicSlug?: StringNullableWithAggregatesFilter<"SyncJob"> | string | null
    articleId?: StringNullableWithAggregatesFilter<"SyncJob"> | string | null
    status?: StringWithAggregatesFilter<"SyncJob"> | string
    priority?: IntWithAggregatesFilter<"SyncJob"> | number
    attempts?: IntWithAggregatesFilter<"SyncJob"> | number
    maxAttempts?: IntWithAggregatesFilter<"SyncJob"> | number
    scheduledAt?: DateTimeWithAggregatesFilter<"SyncJob"> | Date | string
    startedAt?: DateTimeNullableWithAggregatesFilter<"SyncJob"> | Date | string | null
    completedAt?: DateTimeNullableWithAggregatesFilter<"SyncJob"> | Date | string | null
    result?: StringNullableWithAggregatesFilter<"SyncJob"> | string | null
    error?: StringNullableWithAggregatesFilter<"SyncJob"> | string | null
    createdAt?: DateTimeWithAggregatesFilter<"SyncJob"> | Date | string
    updatedAt?: DateTimeWithAggregatesFilter<"SyncJob"> | Date | string
  }

  export type AccountCreateInput = {
    id?: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token?: string | null
    access_token?: string | null
    expires_at?: number | null
    token_type?: string | null
    scope?: string | null
    id_token?: string | null
    session_state?: string | null
    user: UserCreateNestedOneWithoutAccountsInput
  }

  export type AccountUncheckedCreateInput = {
    id?: string
    userId: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token?: string | null
    access_token?: string | null
    expires_at?: number | null
    token_type?: string | null
    scope?: string | null
    id_token?: string | null
    session_state?: string | null
  }

  export type AccountUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
    user?: UserUpdateOneRequiredWithoutAccountsNestedInput
  }

  export type AccountUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type AccountCreateManyInput = {
    id?: string
    userId: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token?: string | null
    access_token?: string | null
    expires_at?: number | null
    token_type?: string | null
    scope?: string | null
    id_token?: string | null
    session_state?: string | null
  }

  export type AccountUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type AccountUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type SessionCreateInput = {
    id?: string
    sessionToken: string
    expires: Date | string
    user: UserCreateNestedOneWithoutSessionsInput
  }

  export type SessionUncheckedCreateInput = {
    id?: string
    sessionToken: string
    userId: string
    expires: Date | string
  }

  export type SessionUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
    user?: UserUpdateOneRequiredWithoutSessionsNestedInput
  }

  export type SessionUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SessionCreateManyInput = {
    id?: string
    sessionToken: string
    userId: string
    expires: Date | string
  }

  export type SessionUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SessionUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type UserCreateInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
    accounts?: AccountCreateNestedManyWithoutUserInput
    sessions?: SessionCreateNestedManyWithoutUserInput
  }

  export type UserUncheckedCreateInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
    accounts?: AccountUncheckedCreateNestedManyWithoutUserInput
    sessions?: SessionUncheckedCreateNestedManyWithoutUserInput
  }

  export type UserUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
    accounts?: AccountUpdateManyWithoutUserNestedInput
    sessions?: SessionUpdateManyWithoutUserNestedInput
  }

  export type UserUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
    accounts?: AccountUncheckedUpdateManyWithoutUserNestedInput
    sessions?: SessionUncheckedUpdateManyWithoutUserNestedInput
  }

  export type UserCreateManyInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
  }

  export type UserUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type UserUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type VerificationTokenCreateInput = {
    identifier: string
    token: string
    expires: Date | string
  }

  export type VerificationTokenUncheckedCreateInput = {
    identifier: string
    token: string
    expires: Date | string
  }

  export type VerificationTokenUpdateInput = {
    identifier?: StringFieldUpdateOperationsInput | string
    token?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type VerificationTokenUncheckedUpdateInput = {
    identifier?: StringFieldUpdateOperationsInput | string
    token?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type VerificationTokenCreateManyInput = {
    identifier: string
    token: string
    expires: Date | string
  }

  export type VerificationTokenUpdateManyMutationInput = {
    identifier?: StringFieldUpdateOperationsInput | string
    token?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type VerificationTokenUncheckedUpdateManyInput = {
    identifier?: StringFieldUpdateOperationsInput | string
    token?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type EmailVerificationRequestCreateInput = {
    id?: string
    email: string
    createdAt?: Date | string
    invalidated?: boolean
  }

  export type EmailVerificationRequestUncheckedCreateInput = {
    id?: string
    email: string
    createdAt?: Date | string
    invalidated?: boolean
  }

  export type EmailVerificationRequestUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    invalidated?: BoolFieldUpdateOperationsInput | boolean
  }

  export type EmailVerificationRequestUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    invalidated?: BoolFieldUpdateOperationsInput | boolean
  }

  export type EmailVerificationRequestCreateManyInput = {
    id?: string
    email: string
    createdAt?: Date | string
    invalidated?: boolean
  }

  export type EmailVerificationRequestUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    invalidated?: BoolFieldUpdateOperationsInput | boolean
  }

  export type EmailVerificationRequestUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    invalidated?: BoolFieldUpdateOperationsInput | boolean
  }

  export type LocalUserProfileCreateInput = {
    id?: string
    userId: string
    publicId: string
    email: string
    name: string
    hasCompletedOnboarding?: boolean
    topics: string
    topicsDetails?: string | null
    regions: string
    languages: string
    publications: string
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
    feedSyncs?: FeedSyncCreateNestedManyWithoutUserProfileInput
  }

  export type LocalUserProfileUncheckedCreateInput = {
    id?: string
    userId: string
    publicId: string
    email: string
    name: string
    hasCompletedOnboarding?: boolean
    topics: string
    topicsDetails?: string | null
    regions: string
    languages: string
    publications: string
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
    feedSyncs?: FeedSyncUncheckedCreateNestedManyWithoutUserProfileInput
  }

  export type LocalUserProfileUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    publicId?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    hasCompletedOnboarding?: BoolFieldUpdateOperationsInput | boolean
    topics?: StringFieldUpdateOperationsInput | string
    topicsDetails?: NullableStringFieldUpdateOperationsInput | string | null
    regions?: StringFieldUpdateOperationsInput | string
    languages?: StringFieldUpdateOperationsInput | string
    publications?: StringFieldUpdateOperationsInput | string
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedSyncs?: FeedSyncUpdateManyWithoutUserProfileNestedInput
  }

  export type LocalUserProfileUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    publicId?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    hasCompletedOnboarding?: BoolFieldUpdateOperationsInput | boolean
    topics?: StringFieldUpdateOperationsInput | string
    topicsDetails?: NullableStringFieldUpdateOperationsInput | string | null
    regions?: StringFieldUpdateOperationsInput | string
    languages?: StringFieldUpdateOperationsInput | string
    publications?: StringFieldUpdateOperationsInput | string
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedSyncs?: FeedSyncUncheckedUpdateManyWithoutUserProfileNestedInput
  }

  export type LocalUserProfileCreateManyInput = {
    id?: string
    userId: string
    publicId: string
    email: string
    name: string
    hasCompletedOnboarding?: boolean
    topics: string
    topicsDetails?: string | null
    regions: string
    languages: string
    publications: string
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type LocalUserProfileUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    publicId?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    hasCompletedOnboarding?: BoolFieldUpdateOperationsInput | boolean
    topics?: StringFieldUpdateOperationsInput | string
    topicsDetails?: NullableStringFieldUpdateOperationsInput | string | null
    regions?: StringFieldUpdateOperationsInput | string
    languages?: StringFieldUpdateOperationsInput | string
    publications?: StringFieldUpdateOperationsInput | string
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type LocalUserProfileUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    publicId?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    hasCompletedOnboarding?: BoolFieldUpdateOperationsInput | boolean
    topics?: StringFieldUpdateOperationsInput | string
    topicsDetails?: NullableStringFieldUpdateOperationsInput | string | null
    regions?: StringFieldUpdateOperationsInput | string
    languages?: StringFieldUpdateOperationsInput | string
    publications?: StringFieldUpdateOperationsInput | string
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type LocalArticleCreateInput = {
    id?: string
    backendId: string
    title: string
    visualTitle?: string | null
    description: string
    content?: string | null
    url: string
    imageUrl?: string | null
    publishedAt: Date | string
    readTime?: number | null
    isTopHeadline?: boolean
    sourceName: string
    sourceLogoUrl?: string | null
    summary?: string | null
    richContent?: string | null
    contentStatus?: string | null
    contentQuality?: string | null
    topics?: string | null
    isRead?: boolean
    isSaved?: boolean
    readAt?: Date | string | null
    savedAt?: Date | string | null
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
    feedItems?: FeedItemCreateNestedManyWithoutArticleInput
  }

  export type LocalArticleUncheckedCreateInput = {
    id?: string
    backendId: string
    title: string
    visualTitle?: string | null
    description: string
    content?: string | null
    url: string
    imageUrl?: string | null
    publishedAt: Date | string
    readTime?: number | null
    isTopHeadline?: boolean
    sourceName: string
    sourceLogoUrl?: string | null
    summary?: string | null
    richContent?: string | null
    contentStatus?: string | null
    contentQuality?: string | null
    topics?: string | null
    isRead?: boolean
    isSaved?: boolean
    readAt?: Date | string | null
    savedAt?: Date | string | null
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
    feedItems?: FeedItemUncheckedCreateNestedManyWithoutArticleInput
  }

  export type LocalArticleUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    backendId?: StringFieldUpdateOperationsInput | string
    title?: StringFieldUpdateOperationsInput | string
    visualTitle?: NullableStringFieldUpdateOperationsInput | string | null
    description?: StringFieldUpdateOperationsInput | string
    content?: NullableStringFieldUpdateOperationsInput | string | null
    url?: StringFieldUpdateOperationsInput | string
    imageUrl?: NullableStringFieldUpdateOperationsInput | string | null
    publishedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    readTime?: NullableIntFieldUpdateOperationsInput | number | null
    isTopHeadline?: BoolFieldUpdateOperationsInput | boolean
    sourceName?: StringFieldUpdateOperationsInput | string
    sourceLogoUrl?: NullableStringFieldUpdateOperationsInput | string | null
    summary?: NullableStringFieldUpdateOperationsInput | string | null
    richContent?: NullableStringFieldUpdateOperationsInput | string | null
    contentStatus?: NullableStringFieldUpdateOperationsInput | string | null
    contentQuality?: NullableStringFieldUpdateOperationsInput | string | null
    topics?: NullableStringFieldUpdateOperationsInput | string | null
    isRead?: BoolFieldUpdateOperationsInput | boolean
    isSaved?: BoolFieldUpdateOperationsInput | boolean
    readAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    savedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedItems?: FeedItemUpdateManyWithoutArticleNestedInput
  }

  export type LocalArticleUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    backendId?: StringFieldUpdateOperationsInput | string
    title?: StringFieldUpdateOperationsInput | string
    visualTitle?: NullableStringFieldUpdateOperationsInput | string | null
    description?: StringFieldUpdateOperationsInput | string
    content?: NullableStringFieldUpdateOperationsInput | string | null
    url?: StringFieldUpdateOperationsInput | string
    imageUrl?: NullableStringFieldUpdateOperationsInput | string | null
    publishedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    readTime?: NullableIntFieldUpdateOperationsInput | number | null
    isTopHeadline?: BoolFieldUpdateOperationsInput | boolean
    sourceName?: StringFieldUpdateOperationsInput | string
    sourceLogoUrl?: NullableStringFieldUpdateOperationsInput | string | null
    summary?: NullableStringFieldUpdateOperationsInput | string | null
    richContent?: NullableStringFieldUpdateOperationsInput | string | null
    contentStatus?: NullableStringFieldUpdateOperationsInput | string | null
    contentQuality?: NullableStringFieldUpdateOperationsInput | string | null
    topics?: NullableStringFieldUpdateOperationsInput | string | null
    isRead?: BoolFieldUpdateOperationsInput | boolean
    isSaved?: BoolFieldUpdateOperationsInput | boolean
    readAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    savedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedItems?: FeedItemUncheckedUpdateManyWithoutArticleNestedInput
  }

  export type LocalArticleCreateManyInput = {
    id?: string
    backendId: string
    title: string
    visualTitle?: string | null
    description: string
    content?: string | null
    url: string
    imageUrl?: string | null
    publishedAt: Date | string
    readTime?: number | null
    isTopHeadline?: boolean
    sourceName: string
    sourceLogoUrl?: string | null
    summary?: string | null
    richContent?: string | null
    contentStatus?: string | null
    contentQuality?: string | null
    topics?: string | null
    isRead?: boolean
    isSaved?: boolean
    readAt?: Date | string | null
    savedAt?: Date | string | null
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type LocalArticleUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    backendId?: StringFieldUpdateOperationsInput | string
    title?: StringFieldUpdateOperationsInput | string
    visualTitle?: NullableStringFieldUpdateOperationsInput | string | null
    description?: StringFieldUpdateOperationsInput | string
    content?: NullableStringFieldUpdateOperationsInput | string | null
    url?: StringFieldUpdateOperationsInput | string
    imageUrl?: NullableStringFieldUpdateOperationsInput | string | null
    publishedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    readTime?: NullableIntFieldUpdateOperationsInput | number | null
    isTopHeadline?: BoolFieldUpdateOperationsInput | boolean
    sourceName?: StringFieldUpdateOperationsInput | string
    sourceLogoUrl?: NullableStringFieldUpdateOperationsInput | string | null
    summary?: NullableStringFieldUpdateOperationsInput | string | null
    richContent?: NullableStringFieldUpdateOperationsInput | string | null
    contentStatus?: NullableStringFieldUpdateOperationsInput | string | null
    contentQuality?: NullableStringFieldUpdateOperationsInput | string | null
    topics?: NullableStringFieldUpdateOperationsInput | string | null
    isRead?: BoolFieldUpdateOperationsInput | boolean
    isSaved?: BoolFieldUpdateOperationsInput | boolean
    readAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    savedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type LocalArticleUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    backendId?: StringFieldUpdateOperationsInput | string
    title?: StringFieldUpdateOperationsInput | string
    visualTitle?: NullableStringFieldUpdateOperationsInput | string | null
    description?: StringFieldUpdateOperationsInput | string
    content?: NullableStringFieldUpdateOperationsInput | string | null
    url?: StringFieldUpdateOperationsInput | string
    imageUrl?: NullableStringFieldUpdateOperationsInput | string | null
    publishedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    readTime?: NullableIntFieldUpdateOperationsInput | number | null
    isTopHeadline?: BoolFieldUpdateOperationsInput | boolean
    sourceName?: StringFieldUpdateOperationsInput | string
    sourceLogoUrl?: NullableStringFieldUpdateOperationsInput | string | null
    summary?: NullableStringFieldUpdateOperationsInput | string | null
    richContent?: NullableStringFieldUpdateOperationsInput | string | null
    contentStatus?: NullableStringFieldUpdateOperationsInput | string | null
    contentQuality?: NullableStringFieldUpdateOperationsInput | string | null
    topics?: NullableStringFieldUpdateOperationsInput | string | null
    isRead?: BoolFieldUpdateOperationsInput | boolean
    isSaved?: BoolFieldUpdateOperationsInput | boolean
    readAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    savedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedSyncCreateInput = {
    id?: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    userProfile: LocalUserProfileCreateNestedOneWithoutFeedSyncsInput
    feedItems?: FeedItemCreateNestedManyWithoutFeedSyncInput
  }

  export type FeedSyncUncheckedCreateInput = {
    id?: string
    userId: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    feedItems?: FeedItemUncheckedCreateNestedManyWithoutFeedSyncInput
  }

  export type FeedSyncUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    userProfile?: LocalUserProfileUpdateOneRequiredWithoutFeedSyncsNestedInput
    feedItems?: FeedItemUpdateManyWithoutFeedSyncNestedInput
  }

  export type FeedSyncUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedItems?: FeedItemUncheckedUpdateManyWithoutFeedSyncNestedInput
  }

  export type FeedSyncCreateManyInput = {
    id?: string
    userId: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type FeedSyncUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedSyncUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemCreateInput = {
    id?: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
    feedSync: FeedSyncCreateNestedOneWithoutFeedItemsInput
    article: LocalArticleCreateNestedOneWithoutFeedItemsInput
  }

  export type FeedItemUncheckedCreateInput = {
    id?: string
    feedSyncId: string
    articleId: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
  }

  export type FeedItemUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedSync?: FeedSyncUpdateOneRequiredWithoutFeedItemsNestedInput
    article?: LocalArticleUpdateOneRequiredWithoutFeedItemsNestedInput
  }

  export type FeedItemUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedSyncId?: StringFieldUpdateOperationsInput | string
    articleId?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemCreateManyInput = {
    id?: string
    feedSyncId: string
    articleId: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
  }

  export type FeedItemUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedSyncId?: StringFieldUpdateOperationsInput | string
    articleId?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SyncJobCreateInput = {
    id?: string
    type: string
    userId?: string | null
    feedType?: string | null
    topicSlug?: string | null
    articleId?: string | null
    status: string
    priority?: number
    attempts?: number
    maxAttempts?: number
    scheduledAt: Date | string
    startedAt?: Date | string | null
    completedAt?: Date | string | null
    result?: string | null
    error?: string | null
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type SyncJobUncheckedCreateInput = {
    id?: string
    type: string
    userId?: string | null
    feedType?: string | null
    topicSlug?: string | null
    articleId?: string | null
    status: string
    priority?: number
    attempts?: number
    maxAttempts?: number
    scheduledAt: Date | string
    startedAt?: Date | string | null
    completedAt?: Date | string | null
    result?: string | null
    error?: string | null
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type SyncJobUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    userId?: NullableStringFieldUpdateOperationsInput | string | null
    feedType?: NullableStringFieldUpdateOperationsInput | string | null
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    articleId?: NullableStringFieldUpdateOperationsInput | string | null
    status?: StringFieldUpdateOperationsInput | string
    priority?: IntFieldUpdateOperationsInput | number
    attempts?: IntFieldUpdateOperationsInput | number
    maxAttempts?: IntFieldUpdateOperationsInput | number
    scheduledAt?: DateTimeFieldUpdateOperationsInput | Date | string
    startedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    completedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    result?: NullableStringFieldUpdateOperationsInput | string | null
    error?: NullableStringFieldUpdateOperationsInput | string | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SyncJobUncheckedUpdateInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    userId?: NullableStringFieldUpdateOperationsInput | string | null
    feedType?: NullableStringFieldUpdateOperationsInput | string | null
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    articleId?: NullableStringFieldUpdateOperationsInput | string | null
    status?: StringFieldUpdateOperationsInput | string
    priority?: IntFieldUpdateOperationsInput | number
    attempts?: IntFieldUpdateOperationsInput | number
    maxAttempts?: IntFieldUpdateOperationsInput | number
    scheduledAt?: DateTimeFieldUpdateOperationsInput | Date | string
    startedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    completedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    result?: NullableStringFieldUpdateOperationsInput | string | null
    error?: NullableStringFieldUpdateOperationsInput | string | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SyncJobCreateManyInput = {
    id?: string
    type: string
    userId?: string | null
    feedType?: string | null
    topicSlug?: string | null
    articleId?: string | null
    status: string
    priority?: number
    attempts?: number
    maxAttempts?: number
    scheduledAt: Date | string
    startedAt?: Date | string | null
    completedAt?: Date | string | null
    result?: string | null
    error?: string | null
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type SyncJobUpdateManyMutationInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    userId?: NullableStringFieldUpdateOperationsInput | string | null
    feedType?: NullableStringFieldUpdateOperationsInput | string | null
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    articleId?: NullableStringFieldUpdateOperationsInput | string | null
    status?: StringFieldUpdateOperationsInput | string
    priority?: IntFieldUpdateOperationsInput | number
    attempts?: IntFieldUpdateOperationsInput | number
    maxAttempts?: IntFieldUpdateOperationsInput | number
    scheduledAt?: DateTimeFieldUpdateOperationsInput | Date | string
    startedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    completedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    result?: NullableStringFieldUpdateOperationsInput | string | null
    error?: NullableStringFieldUpdateOperationsInput | string | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SyncJobUncheckedUpdateManyInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    userId?: NullableStringFieldUpdateOperationsInput | string | null
    feedType?: NullableStringFieldUpdateOperationsInput | string | null
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    articleId?: NullableStringFieldUpdateOperationsInput | string | null
    status?: StringFieldUpdateOperationsInput | string
    priority?: IntFieldUpdateOperationsInput | number
    attempts?: IntFieldUpdateOperationsInput | number
    maxAttempts?: IntFieldUpdateOperationsInput | number
    scheduledAt?: DateTimeFieldUpdateOperationsInput | Date | string
    startedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    completedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    result?: NullableStringFieldUpdateOperationsInput | string | null
    error?: NullableStringFieldUpdateOperationsInput | string | null
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type StringFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[]
    notIn?: string[]
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringFilter<$PrismaModel> | string
  }

  export type StringNullableFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | null
    notIn?: string[] | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringNullableFilter<$PrismaModel> | string | null
  }

  export type IntNullableFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableFilter<$PrismaModel> | number | null
  }

  export type UserScalarRelationFilter = {
    is?: UserWhereInput
    isNot?: UserWhereInput
  }

  export type SortOrderInput = {
    sort: SortOrder
    nulls?: NullsOrder
  }

  export type AccountProviderProviderAccountIdCompoundUniqueInput = {
    provider: string
    providerAccountId: string
  }

  export type AccountCountOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    type?: SortOrder
    provider?: SortOrder
    providerAccountId?: SortOrder
    refresh_token?: SortOrder
    access_token?: SortOrder
    expires_at?: SortOrder
    token_type?: SortOrder
    scope?: SortOrder
    id_token?: SortOrder
    session_state?: SortOrder
  }

  export type AccountAvgOrderByAggregateInput = {
    expires_at?: SortOrder
  }

  export type AccountMaxOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    type?: SortOrder
    provider?: SortOrder
    providerAccountId?: SortOrder
    refresh_token?: SortOrder
    access_token?: SortOrder
    expires_at?: SortOrder
    token_type?: SortOrder
    scope?: SortOrder
    id_token?: SortOrder
    session_state?: SortOrder
  }

  export type AccountMinOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    type?: SortOrder
    provider?: SortOrder
    providerAccountId?: SortOrder
    refresh_token?: SortOrder
    access_token?: SortOrder
    expires_at?: SortOrder
    token_type?: SortOrder
    scope?: SortOrder
    id_token?: SortOrder
    session_state?: SortOrder
  }

  export type AccountSumOrderByAggregateInput = {
    expires_at?: SortOrder
  }

  export type StringWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[]
    notIn?: string[]
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringWithAggregatesFilter<$PrismaModel> | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedStringFilter<$PrismaModel>
    _max?: NestedStringFilter<$PrismaModel>
  }

  export type StringNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | null
    notIn?: string[] | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringNullableWithAggregatesFilter<$PrismaModel> | string | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedStringNullableFilter<$PrismaModel>
    _max?: NestedStringNullableFilter<$PrismaModel>
  }

  export type IntNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedIntNullableFilter<$PrismaModel>
    _max?: NestedIntNullableFilter<$PrismaModel>
  }

  export type DateTimeFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[]
    notIn?: Date[] | string[]
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeFilter<$PrismaModel> | Date | string
  }

  export type SessionCountOrderByAggregateInput = {
    id?: SortOrder
    sessionToken?: SortOrder
    userId?: SortOrder
    expires?: SortOrder
  }

  export type SessionMaxOrderByAggregateInput = {
    id?: SortOrder
    sessionToken?: SortOrder
    userId?: SortOrder
    expires?: SortOrder
  }

  export type SessionMinOrderByAggregateInput = {
    id?: SortOrder
    sessionToken?: SortOrder
    userId?: SortOrder
    expires?: SortOrder
  }

  export type DateTimeWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[]
    notIn?: Date[] | string[]
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeWithAggregatesFilter<$PrismaModel> | Date | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedDateTimeFilter<$PrismaModel>
    _max?: NestedDateTimeFilter<$PrismaModel>
  }

  export type DateTimeNullableFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel> | null
    in?: Date[] | string[] | null
    notIn?: Date[] | string[] | null
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeNullableFilter<$PrismaModel> | Date | string | null
  }

  export type AccountListRelationFilter = {
    every?: AccountWhereInput
    some?: AccountWhereInput
    none?: AccountWhereInput
  }

  export type SessionListRelationFilter = {
    every?: SessionWhereInput
    some?: SessionWhereInput
    none?: SessionWhereInput
  }

  export type AccountOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type SessionOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type UserCountOrderByAggregateInput = {
    id?: SortOrder
    name?: SortOrder
    email?: SortOrder
    emailVerified?: SortOrder
    image?: SortOrder
  }

  export type UserMaxOrderByAggregateInput = {
    id?: SortOrder
    name?: SortOrder
    email?: SortOrder
    emailVerified?: SortOrder
    image?: SortOrder
  }

  export type UserMinOrderByAggregateInput = {
    id?: SortOrder
    name?: SortOrder
    email?: SortOrder
    emailVerified?: SortOrder
    image?: SortOrder
  }

  export type DateTimeNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel> | null
    in?: Date[] | string[] | null
    notIn?: Date[] | string[] | null
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeNullableWithAggregatesFilter<$PrismaModel> | Date | string | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedDateTimeNullableFilter<$PrismaModel>
    _max?: NestedDateTimeNullableFilter<$PrismaModel>
  }

  export type VerificationTokenIdentifierTokenCompoundUniqueInput = {
    identifier: string
    token: string
  }

  export type VerificationTokenCountOrderByAggregateInput = {
    identifier?: SortOrder
    token?: SortOrder
    expires?: SortOrder
  }

  export type VerificationTokenMaxOrderByAggregateInput = {
    identifier?: SortOrder
    token?: SortOrder
    expires?: SortOrder
  }

  export type VerificationTokenMinOrderByAggregateInput = {
    identifier?: SortOrder
    token?: SortOrder
    expires?: SortOrder
  }

  export type BoolFilter<$PrismaModel = never> = {
    equals?: boolean | BooleanFieldRefInput<$PrismaModel>
    not?: NestedBoolFilter<$PrismaModel> | boolean
  }

  export type EmailVerificationRequestCountOrderByAggregateInput = {
    id?: SortOrder
    email?: SortOrder
    createdAt?: SortOrder
    invalidated?: SortOrder
  }

  export type EmailVerificationRequestMaxOrderByAggregateInput = {
    id?: SortOrder
    email?: SortOrder
    createdAt?: SortOrder
    invalidated?: SortOrder
  }

  export type EmailVerificationRequestMinOrderByAggregateInput = {
    id?: SortOrder
    email?: SortOrder
    createdAt?: SortOrder
    invalidated?: SortOrder
  }

  export type BoolWithAggregatesFilter<$PrismaModel = never> = {
    equals?: boolean | BooleanFieldRefInput<$PrismaModel>
    not?: NestedBoolWithAggregatesFilter<$PrismaModel> | boolean
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedBoolFilter<$PrismaModel>
    _max?: NestedBoolFilter<$PrismaModel>
  }

  export type FeedSyncListRelationFilter = {
    every?: FeedSyncWhereInput
    some?: FeedSyncWhereInput
    none?: FeedSyncWhereInput
  }

  export type FeedSyncOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type LocalUserProfileCountOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    publicId?: SortOrder
    email?: SortOrder
    name?: SortOrder
    hasCompletedOnboarding?: SortOrder
    topics?: SortOrder
    topicsDetails?: SortOrder
    regions?: SortOrder
    languages?: SortOrder
    publications?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type LocalUserProfileMaxOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    publicId?: SortOrder
    email?: SortOrder
    name?: SortOrder
    hasCompletedOnboarding?: SortOrder
    topics?: SortOrder
    topicsDetails?: SortOrder
    regions?: SortOrder
    languages?: SortOrder
    publications?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type LocalUserProfileMinOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    publicId?: SortOrder
    email?: SortOrder
    name?: SortOrder
    hasCompletedOnboarding?: SortOrder
    topics?: SortOrder
    topicsDetails?: SortOrder
    regions?: SortOrder
    languages?: SortOrder
    publications?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type FeedItemListRelationFilter = {
    every?: FeedItemWhereInput
    some?: FeedItemWhereInput
    none?: FeedItemWhereInput
  }

  export type FeedItemOrderByRelationAggregateInput = {
    _count?: SortOrder
  }

  export type LocalArticleCountOrderByAggregateInput = {
    id?: SortOrder
    backendId?: SortOrder
    title?: SortOrder
    visualTitle?: SortOrder
    description?: SortOrder
    content?: SortOrder
    url?: SortOrder
    imageUrl?: SortOrder
    publishedAt?: SortOrder
    readTime?: SortOrder
    isTopHeadline?: SortOrder
    sourceName?: SortOrder
    sourceLogoUrl?: SortOrder
    summary?: SortOrder
    richContent?: SortOrder
    contentStatus?: SortOrder
    contentQuality?: SortOrder
    topics?: SortOrder
    isRead?: SortOrder
    isSaved?: SortOrder
    readAt?: SortOrder
    savedAt?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type LocalArticleAvgOrderByAggregateInput = {
    readTime?: SortOrder
  }

  export type LocalArticleMaxOrderByAggregateInput = {
    id?: SortOrder
    backendId?: SortOrder
    title?: SortOrder
    visualTitle?: SortOrder
    description?: SortOrder
    content?: SortOrder
    url?: SortOrder
    imageUrl?: SortOrder
    publishedAt?: SortOrder
    readTime?: SortOrder
    isTopHeadline?: SortOrder
    sourceName?: SortOrder
    sourceLogoUrl?: SortOrder
    summary?: SortOrder
    richContent?: SortOrder
    contentStatus?: SortOrder
    contentQuality?: SortOrder
    topics?: SortOrder
    isRead?: SortOrder
    isSaved?: SortOrder
    readAt?: SortOrder
    savedAt?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type LocalArticleMinOrderByAggregateInput = {
    id?: SortOrder
    backendId?: SortOrder
    title?: SortOrder
    visualTitle?: SortOrder
    description?: SortOrder
    content?: SortOrder
    url?: SortOrder
    imageUrl?: SortOrder
    publishedAt?: SortOrder
    readTime?: SortOrder
    isTopHeadline?: SortOrder
    sourceName?: SortOrder
    sourceLogoUrl?: SortOrder
    summary?: SortOrder
    richContent?: SortOrder
    contentStatus?: SortOrder
    contentQuality?: SortOrder
    topics?: SortOrder
    isRead?: SortOrder
    isSaved?: SortOrder
    readAt?: SortOrder
    savedAt?: SortOrder
    lastSyncAt?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type LocalArticleSumOrderByAggregateInput = {
    readTime?: SortOrder
  }

  export type IntFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[]
    notIn?: number[]
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntFilter<$PrismaModel> | number
  }

  export type LocalUserProfileScalarRelationFilter = {
    is?: LocalUserProfileWhereInput
    isNot?: LocalUserProfileWhereInput
  }

  export type FeedSyncUserIdFeedTypeTopicSlugCompoundUniqueInput = {
    userId: string
    feedType: string
    topicSlug: string
  }

  export type FeedSyncCountOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrder
    lastSyncAt?: SortOrder
    nextSyncAt?: SortOrder
    isStale?: SortOrder
    syncInProgress?: SortOrder
    lastPage?: SortOrder
    hasMore?: SortOrder
    totalItems?: SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrder
    lastError?: SortOrder
    consecutiveErrors?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type FeedSyncAvgOrderByAggregateInput = {
    lastPage?: SortOrder
    totalItems?: SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrder
    consecutiveErrors?: SortOrder
  }

  export type FeedSyncMaxOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrder
    lastSyncAt?: SortOrder
    nextSyncAt?: SortOrder
    isStale?: SortOrder
    syncInProgress?: SortOrder
    lastPage?: SortOrder
    hasMore?: SortOrder
    totalItems?: SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrder
    lastError?: SortOrder
    consecutiveErrors?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type FeedSyncMinOrderByAggregateInput = {
    id?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrder
    lastSyncAt?: SortOrder
    nextSyncAt?: SortOrder
    isStale?: SortOrder
    syncInProgress?: SortOrder
    lastPage?: SortOrder
    hasMore?: SortOrder
    totalItems?: SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrder
    lastError?: SortOrder
    consecutiveErrors?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type FeedSyncSumOrderByAggregateInput = {
    lastPage?: SortOrder
    totalItems?: SortOrder
    syncCount?: SortOrder
    lastSyncDuration?: SortOrder
    consecutiveErrors?: SortOrder
  }

  export type IntWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[]
    notIn?: number[]
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntWithAggregatesFilter<$PrismaModel> | number
    _count?: NestedIntFilter<$PrismaModel>
    _avg?: NestedFloatFilter<$PrismaModel>
    _sum?: NestedIntFilter<$PrismaModel>
    _min?: NestedIntFilter<$PrismaModel>
    _max?: NestedIntFilter<$PrismaModel>
  }

  export type FloatNullableFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableFilter<$PrismaModel> | number | null
  }

  export type FeedSyncScalarRelationFilter = {
    is?: FeedSyncWhereInput
    isNot?: FeedSyncWhereInput
  }

  export type LocalArticleScalarRelationFilter = {
    is?: LocalArticleWhereInput
    isNot?: LocalArticleWhereInput
  }

  export type FeedItemFeedSyncIdArticleIdCompoundUniqueInput = {
    feedSyncId: string
    articleId: string
  }

  export type FeedItemCountOrderByAggregateInput = {
    id?: SortOrder
    feedSyncId?: SortOrder
    articleId?: SortOrder
    position?: SortOrder
    relevanceScore?: SortOrder
    addedAt?: SortOrder
  }

  export type FeedItemAvgOrderByAggregateInput = {
    position?: SortOrder
    relevanceScore?: SortOrder
  }

  export type FeedItemMaxOrderByAggregateInput = {
    id?: SortOrder
    feedSyncId?: SortOrder
    articleId?: SortOrder
    position?: SortOrder
    relevanceScore?: SortOrder
    addedAt?: SortOrder
  }

  export type FeedItemMinOrderByAggregateInput = {
    id?: SortOrder
    feedSyncId?: SortOrder
    articleId?: SortOrder
    position?: SortOrder
    relevanceScore?: SortOrder
    addedAt?: SortOrder
  }

  export type FeedItemSumOrderByAggregateInput = {
    position?: SortOrder
    relevanceScore?: SortOrder
  }

  export type FloatNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedFloatNullableFilter<$PrismaModel>
    _min?: NestedFloatNullableFilter<$PrismaModel>
    _max?: NestedFloatNullableFilter<$PrismaModel>
  }

  export type SyncJobCountOrderByAggregateInput = {
    id?: SortOrder
    type?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrder
    articleId?: SortOrder
    status?: SortOrder
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
    scheduledAt?: SortOrder
    startedAt?: SortOrder
    completedAt?: SortOrder
    result?: SortOrder
    error?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type SyncJobAvgOrderByAggregateInput = {
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
  }

  export type SyncJobMaxOrderByAggregateInput = {
    id?: SortOrder
    type?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrder
    articleId?: SortOrder
    status?: SortOrder
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
    scheduledAt?: SortOrder
    startedAt?: SortOrder
    completedAt?: SortOrder
    result?: SortOrder
    error?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type SyncJobMinOrderByAggregateInput = {
    id?: SortOrder
    type?: SortOrder
    userId?: SortOrder
    feedType?: SortOrder
    topicSlug?: SortOrder
    articleId?: SortOrder
    status?: SortOrder
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
    scheduledAt?: SortOrder
    startedAt?: SortOrder
    completedAt?: SortOrder
    result?: SortOrder
    error?: SortOrder
    createdAt?: SortOrder
    updatedAt?: SortOrder
  }

  export type SyncJobSumOrderByAggregateInput = {
    priority?: SortOrder
    attempts?: SortOrder
    maxAttempts?: SortOrder
  }

  export type UserCreateNestedOneWithoutAccountsInput = {
    create?: XOR<UserCreateWithoutAccountsInput, UserUncheckedCreateWithoutAccountsInput>
    connectOrCreate?: UserCreateOrConnectWithoutAccountsInput
    connect?: UserWhereUniqueInput
  }

  export type StringFieldUpdateOperationsInput = {
    set?: string
  }

  export type NullableStringFieldUpdateOperationsInput = {
    set?: string | null
  }

  export type NullableIntFieldUpdateOperationsInput = {
    set?: number | null
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type UserUpdateOneRequiredWithoutAccountsNestedInput = {
    create?: XOR<UserCreateWithoutAccountsInput, UserUncheckedCreateWithoutAccountsInput>
    connectOrCreate?: UserCreateOrConnectWithoutAccountsInput
    upsert?: UserUpsertWithoutAccountsInput
    connect?: UserWhereUniqueInput
    update?: XOR<XOR<UserUpdateToOneWithWhereWithoutAccountsInput, UserUpdateWithoutAccountsInput>, UserUncheckedUpdateWithoutAccountsInput>
  }

  export type UserCreateNestedOneWithoutSessionsInput = {
    create?: XOR<UserCreateWithoutSessionsInput, UserUncheckedCreateWithoutSessionsInput>
    connectOrCreate?: UserCreateOrConnectWithoutSessionsInput
    connect?: UserWhereUniqueInput
  }

  export type DateTimeFieldUpdateOperationsInput = {
    set?: Date | string
  }

  export type UserUpdateOneRequiredWithoutSessionsNestedInput = {
    create?: XOR<UserCreateWithoutSessionsInput, UserUncheckedCreateWithoutSessionsInput>
    connectOrCreate?: UserCreateOrConnectWithoutSessionsInput
    upsert?: UserUpsertWithoutSessionsInput
    connect?: UserWhereUniqueInput
    update?: XOR<XOR<UserUpdateToOneWithWhereWithoutSessionsInput, UserUpdateWithoutSessionsInput>, UserUncheckedUpdateWithoutSessionsInput>
  }

  export type AccountCreateNestedManyWithoutUserInput = {
    create?: XOR<AccountCreateWithoutUserInput, AccountUncheckedCreateWithoutUserInput> | AccountCreateWithoutUserInput[] | AccountUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AccountCreateOrConnectWithoutUserInput | AccountCreateOrConnectWithoutUserInput[]
    createMany?: AccountCreateManyUserInputEnvelope
    connect?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
  }

  export type SessionCreateNestedManyWithoutUserInput = {
    create?: XOR<SessionCreateWithoutUserInput, SessionUncheckedCreateWithoutUserInput> | SessionCreateWithoutUserInput[] | SessionUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SessionCreateOrConnectWithoutUserInput | SessionCreateOrConnectWithoutUserInput[]
    createMany?: SessionCreateManyUserInputEnvelope
    connect?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
  }

  export type AccountUncheckedCreateNestedManyWithoutUserInput = {
    create?: XOR<AccountCreateWithoutUserInput, AccountUncheckedCreateWithoutUserInput> | AccountCreateWithoutUserInput[] | AccountUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AccountCreateOrConnectWithoutUserInput | AccountCreateOrConnectWithoutUserInput[]
    createMany?: AccountCreateManyUserInputEnvelope
    connect?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
  }

  export type SessionUncheckedCreateNestedManyWithoutUserInput = {
    create?: XOR<SessionCreateWithoutUserInput, SessionUncheckedCreateWithoutUserInput> | SessionCreateWithoutUserInput[] | SessionUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SessionCreateOrConnectWithoutUserInput | SessionCreateOrConnectWithoutUserInput[]
    createMany?: SessionCreateManyUserInputEnvelope
    connect?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
  }

  export type NullableDateTimeFieldUpdateOperationsInput = {
    set?: Date | string | null
  }

  export type AccountUpdateManyWithoutUserNestedInput = {
    create?: XOR<AccountCreateWithoutUserInput, AccountUncheckedCreateWithoutUserInput> | AccountCreateWithoutUserInput[] | AccountUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AccountCreateOrConnectWithoutUserInput | AccountCreateOrConnectWithoutUserInput[]
    upsert?: AccountUpsertWithWhereUniqueWithoutUserInput | AccountUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: AccountCreateManyUserInputEnvelope
    set?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    disconnect?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    delete?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    connect?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    update?: AccountUpdateWithWhereUniqueWithoutUserInput | AccountUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: AccountUpdateManyWithWhereWithoutUserInput | AccountUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: AccountScalarWhereInput | AccountScalarWhereInput[]
  }

  export type SessionUpdateManyWithoutUserNestedInput = {
    create?: XOR<SessionCreateWithoutUserInput, SessionUncheckedCreateWithoutUserInput> | SessionCreateWithoutUserInput[] | SessionUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SessionCreateOrConnectWithoutUserInput | SessionCreateOrConnectWithoutUserInput[]
    upsert?: SessionUpsertWithWhereUniqueWithoutUserInput | SessionUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: SessionCreateManyUserInputEnvelope
    set?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    disconnect?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    delete?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    connect?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    update?: SessionUpdateWithWhereUniqueWithoutUserInput | SessionUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: SessionUpdateManyWithWhereWithoutUserInput | SessionUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: SessionScalarWhereInput | SessionScalarWhereInput[]
  }

  export type AccountUncheckedUpdateManyWithoutUserNestedInput = {
    create?: XOR<AccountCreateWithoutUserInput, AccountUncheckedCreateWithoutUserInput> | AccountCreateWithoutUserInput[] | AccountUncheckedCreateWithoutUserInput[]
    connectOrCreate?: AccountCreateOrConnectWithoutUserInput | AccountCreateOrConnectWithoutUserInput[]
    upsert?: AccountUpsertWithWhereUniqueWithoutUserInput | AccountUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: AccountCreateManyUserInputEnvelope
    set?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    disconnect?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    delete?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    connect?: AccountWhereUniqueInput | AccountWhereUniqueInput[]
    update?: AccountUpdateWithWhereUniqueWithoutUserInput | AccountUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: AccountUpdateManyWithWhereWithoutUserInput | AccountUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: AccountScalarWhereInput | AccountScalarWhereInput[]
  }

  export type SessionUncheckedUpdateManyWithoutUserNestedInput = {
    create?: XOR<SessionCreateWithoutUserInput, SessionUncheckedCreateWithoutUserInput> | SessionCreateWithoutUserInput[] | SessionUncheckedCreateWithoutUserInput[]
    connectOrCreate?: SessionCreateOrConnectWithoutUserInput | SessionCreateOrConnectWithoutUserInput[]
    upsert?: SessionUpsertWithWhereUniqueWithoutUserInput | SessionUpsertWithWhereUniqueWithoutUserInput[]
    createMany?: SessionCreateManyUserInputEnvelope
    set?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    disconnect?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    delete?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    connect?: SessionWhereUniqueInput | SessionWhereUniqueInput[]
    update?: SessionUpdateWithWhereUniqueWithoutUserInput | SessionUpdateWithWhereUniqueWithoutUserInput[]
    updateMany?: SessionUpdateManyWithWhereWithoutUserInput | SessionUpdateManyWithWhereWithoutUserInput[]
    deleteMany?: SessionScalarWhereInput | SessionScalarWhereInput[]
  }

  export type BoolFieldUpdateOperationsInput = {
    set?: boolean
  }

  export type FeedSyncCreateNestedManyWithoutUserProfileInput = {
    create?: XOR<FeedSyncCreateWithoutUserProfileInput, FeedSyncUncheckedCreateWithoutUserProfileInput> | FeedSyncCreateWithoutUserProfileInput[] | FeedSyncUncheckedCreateWithoutUserProfileInput[]
    connectOrCreate?: FeedSyncCreateOrConnectWithoutUserProfileInput | FeedSyncCreateOrConnectWithoutUserProfileInput[]
    createMany?: FeedSyncCreateManyUserProfileInputEnvelope
    connect?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
  }

  export type FeedSyncUncheckedCreateNestedManyWithoutUserProfileInput = {
    create?: XOR<FeedSyncCreateWithoutUserProfileInput, FeedSyncUncheckedCreateWithoutUserProfileInput> | FeedSyncCreateWithoutUserProfileInput[] | FeedSyncUncheckedCreateWithoutUserProfileInput[]
    connectOrCreate?: FeedSyncCreateOrConnectWithoutUserProfileInput | FeedSyncCreateOrConnectWithoutUserProfileInput[]
    createMany?: FeedSyncCreateManyUserProfileInputEnvelope
    connect?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
  }

  export type FeedSyncUpdateManyWithoutUserProfileNestedInput = {
    create?: XOR<FeedSyncCreateWithoutUserProfileInput, FeedSyncUncheckedCreateWithoutUserProfileInput> | FeedSyncCreateWithoutUserProfileInput[] | FeedSyncUncheckedCreateWithoutUserProfileInput[]
    connectOrCreate?: FeedSyncCreateOrConnectWithoutUserProfileInput | FeedSyncCreateOrConnectWithoutUserProfileInput[]
    upsert?: FeedSyncUpsertWithWhereUniqueWithoutUserProfileInput | FeedSyncUpsertWithWhereUniqueWithoutUserProfileInput[]
    createMany?: FeedSyncCreateManyUserProfileInputEnvelope
    set?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    disconnect?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    delete?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    connect?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    update?: FeedSyncUpdateWithWhereUniqueWithoutUserProfileInput | FeedSyncUpdateWithWhereUniqueWithoutUserProfileInput[]
    updateMany?: FeedSyncUpdateManyWithWhereWithoutUserProfileInput | FeedSyncUpdateManyWithWhereWithoutUserProfileInput[]
    deleteMany?: FeedSyncScalarWhereInput | FeedSyncScalarWhereInput[]
  }

  export type FeedSyncUncheckedUpdateManyWithoutUserProfileNestedInput = {
    create?: XOR<FeedSyncCreateWithoutUserProfileInput, FeedSyncUncheckedCreateWithoutUserProfileInput> | FeedSyncCreateWithoutUserProfileInput[] | FeedSyncUncheckedCreateWithoutUserProfileInput[]
    connectOrCreate?: FeedSyncCreateOrConnectWithoutUserProfileInput | FeedSyncCreateOrConnectWithoutUserProfileInput[]
    upsert?: FeedSyncUpsertWithWhereUniqueWithoutUserProfileInput | FeedSyncUpsertWithWhereUniqueWithoutUserProfileInput[]
    createMany?: FeedSyncCreateManyUserProfileInputEnvelope
    set?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    disconnect?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    delete?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    connect?: FeedSyncWhereUniqueInput | FeedSyncWhereUniqueInput[]
    update?: FeedSyncUpdateWithWhereUniqueWithoutUserProfileInput | FeedSyncUpdateWithWhereUniqueWithoutUserProfileInput[]
    updateMany?: FeedSyncUpdateManyWithWhereWithoutUserProfileInput | FeedSyncUpdateManyWithWhereWithoutUserProfileInput[]
    deleteMany?: FeedSyncScalarWhereInput | FeedSyncScalarWhereInput[]
  }

  export type FeedItemCreateNestedManyWithoutArticleInput = {
    create?: XOR<FeedItemCreateWithoutArticleInput, FeedItemUncheckedCreateWithoutArticleInput> | FeedItemCreateWithoutArticleInput[] | FeedItemUncheckedCreateWithoutArticleInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutArticleInput | FeedItemCreateOrConnectWithoutArticleInput[]
    createMany?: FeedItemCreateManyArticleInputEnvelope
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
  }

  export type FeedItemUncheckedCreateNestedManyWithoutArticleInput = {
    create?: XOR<FeedItemCreateWithoutArticleInput, FeedItemUncheckedCreateWithoutArticleInput> | FeedItemCreateWithoutArticleInput[] | FeedItemUncheckedCreateWithoutArticleInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutArticleInput | FeedItemCreateOrConnectWithoutArticleInput[]
    createMany?: FeedItemCreateManyArticleInputEnvelope
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
  }

  export type FeedItemUpdateManyWithoutArticleNestedInput = {
    create?: XOR<FeedItemCreateWithoutArticleInput, FeedItemUncheckedCreateWithoutArticleInput> | FeedItemCreateWithoutArticleInput[] | FeedItemUncheckedCreateWithoutArticleInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutArticleInput | FeedItemCreateOrConnectWithoutArticleInput[]
    upsert?: FeedItemUpsertWithWhereUniqueWithoutArticleInput | FeedItemUpsertWithWhereUniqueWithoutArticleInput[]
    createMany?: FeedItemCreateManyArticleInputEnvelope
    set?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    disconnect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    delete?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    update?: FeedItemUpdateWithWhereUniqueWithoutArticleInput | FeedItemUpdateWithWhereUniqueWithoutArticleInput[]
    updateMany?: FeedItemUpdateManyWithWhereWithoutArticleInput | FeedItemUpdateManyWithWhereWithoutArticleInput[]
    deleteMany?: FeedItemScalarWhereInput | FeedItemScalarWhereInput[]
  }

  export type FeedItemUncheckedUpdateManyWithoutArticleNestedInput = {
    create?: XOR<FeedItemCreateWithoutArticleInput, FeedItemUncheckedCreateWithoutArticleInput> | FeedItemCreateWithoutArticleInput[] | FeedItemUncheckedCreateWithoutArticleInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutArticleInput | FeedItemCreateOrConnectWithoutArticleInput[]
    upsert?: FeedItemUpsertWithWhereUniqueWithoutArticleInput | FeedItemUpsertWithWhereUniqueWithoutArticleInput[]
    createMany?: FeedItemCreateManyArticleInputEnvelope
    set?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    disconnect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    delete?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    update?: FeedItemUpdateWithWhereUniqueWithoutArticleInput | FeedItemUpdateWithWhereUniqueWithoutArticleInput[]
    updateMany?: FeedItemUpdateManyWithWhereWithoutArticleInput | FeedItemUpdateManyWithWhereWithoutArticleInput[]
    deleteMany?: FeedItemScalarWhereInput | FeedItemScalarWhereInput[]
  }

  export type LocalUserProfileCreateNestedOneWithoutFeedSyncsInput = {
    create?: XOR<LocalUserProfileCreateWithoutFeedSyncsInput, LocalUserProfileUncheckedCreateWithoutFeedSyncsInput>
    connectOrCreate?: LocalUserProfileCreateOrConnectWithoutFeedSyncsInput
    connect?: LocalUserProfileWhereUniqueInput
  }

  export type FeedItemCreateNestedManyWithoutFeedSyncInput = {
    create?: XOR<FeedItemCreateWithoutFeedSyncInput, FeedItemUncheckedCreateWithoutFeedSyncInput> | FeedItemCreateWithoutFeedSyncInput[] | FeedItemUncheckedCreateWithoutFeedSyncInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutFeedSyncInput | FeedItemCreateOrConnectWithoutFeedSyncInput[]
    createMany?: FeedItemCreateManyFeedSyncInputEnvelope
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
  }

  export type FeedItemUncheckedCreateNestedManyWithoutFeedSyncInput = {
    create?: XOR<FeedItemCreateWithoutFeedSyncInput, FeedItemUncheckedCreateWithoutFeedSyncInput> | FeedItemCreateWithoutFeedSyncInput[] | FeedItemUncheckedCreateWithoutFeedSyncInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutFeedSyncInput | FeedItemCreateOrConnectWithoutFeedSyncInput[]
    createMany?: FeedItemCreateManyFeedSyncInputEnvelope
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
  }

  export type IntFieldUpdateOperationsInput = {
    set?: number
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type LocalUserProfileUpdateOneRequiredWithoutFeedSyncsNestedInput = {
    create?: XOR<LocalUserProfileCreateWithoutFeedSyncsInput, LocalUserProfileUncheckedCreateWithoutFeedSyncsInput>
    connectOrCreate?: LocalUserProfileCreateOrConnectWithoutFeedSyncsInput
    upsert?: LocalUserProfileUpsertWithoutFeedSyncsInput
    connect?: LocalUserProfileWhereUniqueInput
    update?: XOR<XOR<LocalUserProfileUpdateToOneWithWhereWithoutFeedSyncsInput, LocalUserProfileUpdateWithoutFeedSyncsInput>, LocalUserProfileUncheckedUpdateWithoutFeedSyncsInput>
  }

  export type FeedItemUpdateManyWithoutFeedSyncNestedInput = {
    create?: XOR<FeedItemCreateWithoutFeedSyncInput, FeedItemUncheckedCreateWithoutFeedSyncInput> | FeedItemCreateWithoutFeedSyncInput[] | FeedItemUncheckedCreateWithoutFeedSyncInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutFeedSyncInput | FeedItemCreateOrConnectWithoutFeedSyncInput[]
    upsert?: FeedItemUpsertWithWhereUniqueWithoutFeedSyncInput | FeedItemUpsertWithWhereUniqueWithoutFeedSyncInput[]
    createMany?: FeedItemCreateManyFeedSyncInputEnvelope
    set?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    disconnect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    delete?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    update?: FeedItemUpdateWithWhereUniqueWithoutFeedSyncInput | FeedItemUpdateWithWhereUniqueWithoutFeedSyncInput[]
    updateMany?: FeedItemUpdateManyWithWhereWithoutFeedSyncInput | FeedItemUpdateManyWithWhereWithoutFeedSyncInput[]
    deleteMany?: FeedItemScalarWhereInput | FeedItemScalarWhereInput[]
  }

  export type FeedItemUncheckedUpdateManyWithoutFeedSyncNestedInput = {
    create?: XOR<FeedItemCreateWithoutFeedSyncInput, FeedItemUncheckedCreateWithoutFeedSyncInput> | FeedItemCreateWithoutFeedSyncInput[] | FeedItemUncheckedCreateWithoutFeedSyncInput[]
    connectOrCreate?: FeedItemCreateOrConnectWithoutFeedSyncInput | FeedItemCreateOrConnectWithoutFeedSyncInput[]
    upsert?: FeedItemUpsertWithWhereUniqueWithoutFeedSyncInput | FeedItemUpsertWithWhereUniqueWithoutFeedSyncInput[]
    createMany?: FeedItemCreateManyFeedSyncInputEnvelope
    set?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    disconnect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    delete?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    connect?: FeedItemWhereUniqueInput | FeedItemWhereUniqueInput[]
    update?: FeedItemUpdateWithWhereUniqueWithoutFeedSyncInput | FeedItemUpdateWithWhereUniqueWithoutFeedSyncInput[]
    updateMany?: FeedItemUpdateManyWithWhereWithoutFeedSyncInput | FeedItemUpdateManyWithWhereWithoutFeedSyncInput[]
    deleteMany?: FeedItemScalarWhereInput | FeedItemScalarWhereInput[]
  }

  export type FeedSyncCreateNestedOneWithoutFeedItemsInput = {
    create?: XOR<FeedSyncCreateWithoutFeedItemsInput, FeedSyncUncheckedCreateWithoutFeedItemsInput>
    connectOrCreate?: FeedSyncCreateOrConnectWithoutFeedItemsInput
    connect?: FeedSyncWhereUniqueInput
  }

  export type LocalArticleCreateNestedOneWithoutFeedItemsInput = {
    create?: XOR<LocalArticleCreateWithoutFeedItemsInput, LocalArticleUncheckedCreateWithoutFeedItemsInput>
    connectOrCreate?: LocalArticleCreateOrConnectWithoutFeedItemsInput
    connect?: LocalArticleWhereUniqueInput
  }

  export type NullableFloatFieldUpdateOperationsInput = {
    set?: number | null
    increment?: number
    decrement?: number
    multiply?: number
    divide?: number
  }

  export type FeedSyncUpdateOneRequiredWithoutFeedItemsNestedInput = {
    create?: XOR<FeedSyncCreateWithoutFeedItemsInput, FeedSyncUncheckedCreateWithoutFeedItemsInput>
    connectOrCreate?: FeedSyncCreateOrConnectWithoutFeedItemsInput
    upsert?: FeedSyncUpsertWithoutFeedItemsInput
    connect?: FeedSyncWhereUniqueInput
    update?: XOR<XOR<FeedSyncUpdateToOneWithWhereWithoutFeedItemsInput, FeedSyncUpdateWithoutFeedItemsInput>, FeedSyncUncheckedUpdateWithoutFeedItemsInput>
  }

  export type LocalArticleUpdateOneRequiredWithoutFeedItemsNestedInput = {
    create?: XOR<LocalArticleCreateWithoutFeedItemsInput, LocalArticleUncheckedCreateWithoutFeedItemsInput>
    connectOrCreate?: LocalArticleCreateOrConnectWithoutFeedItemsInput
    upsert?: LocalArticleUpsertWithoutFeedItemsInput
    connect?: LocalArticleWhereUniqueInput
    update?: XOR<XOR<LocalArticleUpdateToOneWithWhereWithoutFeedItemsInput, LocalArticleUpdateWithoutFeedItemsInput>, LocalArticleUncheckedUpdateWithoutFeedItemsInput>
  }

  export type NestedStringFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[]
    notIn?: string[]
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringFilter<$PrismaModel> | string
  }

  export type NestedStringNullableFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | null
    notIn?: string[] | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringNullableFilter<$PrismaModel> | string | null
  }

  export type NestedIntNullableFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableFilter<$PrismaModel> | number | null
  }

  export type NestedStringWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel>
    in?: string[]
    notIn?: string[]
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringWithAggregatesFilter<$PrismaModel> | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedStringFilter<$PrismaModel>
    _max?: NestedStringFilter<$PrismaModel>
  }

  export type NestedIntFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[]
    notIn?: number[]
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntFilter<$PrismaModel> | number
  }

  export type NestedStringNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: string | StringFieldRefInput<$PrismaModel> | null
    in?: string[] | null
    notIn?: string[] | null
    lt?: string | StringFieldRefInput<$PrismaModel>
    lte?: string | StringFieldRefInput<$PrismaModel>
    gt?: string | StringFieldRefInput<$PrismaModel>
    gte?: string | StringFieldRefInput<$PrismaModel>
    contains?: string | StringFieldRefInput<$PrismaModel>
    startsWith?: string | StringFieldRefInput<$PrismaModel>
    endsWith?: string | StringFieldRefInput<$PrismaModel>
    not?: NestedStringNullableWithAggregatesFilter<$PrismaModel> | string | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedStringNullableFilter<$PrismaModel>
    _max?: NestedStringNullableFilter<$PrismaModel>
  }

  export type NestedIntNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedIntNullableFilter<$PrismaModel>
    _max?: NestedIntNullableFilter<$PrismaModel>
  }

  export type NestedFloatNullableFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableFilter<$PrismaModel> | number | null
  }

  export type NestedDateTimeFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[]
    notIn?: Date[] | string[]
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeFilter<$PrismaModel> | Date | string
  }

  export type NestedDateTimeWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    in?: Date[] | string[]
    notIn?: Date[] | string[]
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeWithAggregatesFilter<$PrismaModel> | Date | string
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedDateTimeFilter<$PrismaModel>
    _max?: NestedDateTimeFilter<$PrismaModel>
  }

  export type NestedDateTimeNullableFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel> | null
    in?: Date[] | string[] | null
    notIn?: Date[] | string[] | null
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeNullableFilter<$PrismaModel> | Date | string | null
  }

  export type NestedDateTimeNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: Date | string | DateTimeFieldRefInput<$PrismaModel> | null
    in?: Date[] | string[] | null
    notIn?: Date[] | string[] | null
    lt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    lte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gt?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    gte?: Date | string | DateTimeFieldRefInput<$PrismaModel>
    not?: NestedDateTimeNullableWithAggregatesFilter<$PrismaModel> | Date | string | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _min?: NestedDateTimeNullableFilter<$PrismaModel>
    _max?: NestedDateTimeNullableFilter<$PrismaModel>
  }

  export type NestedBoolFilter<$PrismaModel = never> = {
    equals?: boolean | BooleanFieldRefInput<$PrismaModel>
    not?: NestedBoolFilter<$PrismaModel> | boolean
  }

  export type NestedBoolWithAggregatesFilter<$PrismaModel = never> = {
    equals?: boolean | BooleanFieldRefInput<$PrismaModel>
    not?: NestedBoolWithAggregatesFilter<$PrismaModel> | boolean
    _count?: NestedIntFilter<$PrismaModel>
    _min?: NestedBoolFilter<$PrismaModel>
    _max?: NestedBoolFilter<$PrismaModel>
  }

  export type NestedIntWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | IntFieldRefInput<$PrismaModel>
    in?: number[]
    notIn?: number[]
    lt?: number | IntFieldRefInput<$PrismaModel>
    lte?: number | IntFieldRefInput<$PrismaModel>
    gt?: number | IntFieldRefInput<$PrismaModel>
    gte?: number | IntFieldRefInput<$PrismaModel>
    not?: NestedIntWithAggregatesFilter<$PrismaModel> | number
    _count?: NestedIntFilter<$PrismaModel>
    _avg?: NestedFloatFilter<$PrismaModel>
    _sum?: NestedIntFilter<$PrismaModel>
    _min?: NestedIntFilter<$PrismaModel>
    _max?: NestedIntFilter<$PrismaModel>
  }

  export type NestedFloatFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel>
    in?: number[]
    notIn?: number[]
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatFilter<$PrismaModel> | number
  }

  export type NestedFloatNullableWithAggregatesFilter<$PrismaModel = never> = {
    equals?: number | FloatFieldRefInput<$PrismaModel> | null
    in?: number[] | null
    notIn?: number[] | null
    lt?: number | FloatFieldRefInput<$PrismaModel>
    lte?: number | FloatFieldRefInput<$PrismaModel>
    gt?: number | FloatFieldRefInput<$PrismaModel>
    gte?: number | FloatFieldRefInput<$PrismaModel>
    not?: NestedFloatNullableWithAggregatesFilter<$PrismaModel> | number | null
    _count?: NestedIntNullableFilter<$PrismaModel>
    _avg?: NestedFloatNullableFilter<$PrismaModel>
    _sum?: NestedFloatNullableFilter<$PrismaModel>
    _min?: NestedFloatNullableFilter<$PrismaModel>
    _max?: NestedFloatNullableFilter<$PrismaModel>
  }

  export type UserCreateWithoutAccountsInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
    sessions?: SessionCreateNestedManyWithoutUserInput
  }

  export type UserUncheckedCreateWithoutAccountsInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
    sessions?: SessionUncheckedCreateNestedManyWithoutUserInput
  }

  export type UserCreateOrConnectWithoutAccountsInput = {
    where: UserWhereUniqueInput
    create: XOR<UserCreateWithoutAccountsInput, UserUncheckedCreateWithoutAccountsInput>
  }

  export type UserUpsertWithoutAccountsInput = {
    update: XOR<UserUpdateWithoutAccountsInput, UserUncheckedUpdateWithoutAccountsInput>
    create: XOR<UserCreateWithoutAccountsInput, UserUncheckedCreateWithoutAccountsInput>
    where?: UserWhereInput
  }

  export type UserUpdateToOneWithWhereWithoutAccountsInput = {
    where?: UserWhereInput
    data: XOR<UserUpdateWithoutAccountsInput, UserUncheckedUpdateWithoutAccountsInput>
  }

  export type UserUpdateWithoutAccountsInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
    sessions?: SessionUpdateManyWithoutUserNestedInput
  }

  export type UserUncheckedUpdateWithoutAccountsInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
    sessions?: SessionUncheckedUpdateManyWithoutUserNestedInput
  }

  export type UserCreateWithoutSessionsInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
    accounts?: AccountCreateNestedManyWithoutUserInput
  }

  export type UserUncheckedCreateWithoutSessionsInput = {
    id?: string
    name?: string | null
    email?: string | null
    emailVerified?: Date | string | null
    image?: string | null
    accounts?: AccountUncheckedCreateNestedManyWithoutUserInput
  }

  export type UserCreateOrConnectWithoutSessionsInput = {
    where: UserWhereUniqueInput
    create: XOR<UserCreateWithoutSessionsInput, UserUncheckedCreateWithoutSessionsInput>
  }

  export type UserUpsertWithoutSessionsInput = {
    update: XOR<UserUpdateWithoutSessionsInput, UserUncheckedUpdateWithoutSessionsInput>
    create: XOR<UserCreateWithoutSessionsInput, UserUncheckedCreateWithoutSessionsInput>
    where?: UserWhereInput
  }

  export type UserUpdateToOneWithWhereWithoutSessionsInput = {
    where?: UserWhereInput
    data: XOR<UserUpdateWithoutSessionsInput, UserUncheckedUpdateWithoutSessionsInput>
  }

  export type UserUpdateWithoutSessionsInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
    accounts?: AccountUpdateManyWithoutUserNestedInput
  }

  export type UserUncheckedUpdateWithoutSessionsInput = {
    id?: StringFieldUpdateOperationsInput | string
    name?: NullableStringFieldUpdateOperationsInput | string | null
    email?: NullableStringFieldUpdateOperationsInput | string | null
    emailVerified?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    image?: NullableStringFieldUpdateOperationsInput | string | null
    accounts?: AccountUncheckedUpdateManyWithoutUserNestedInput
  }

  export type AccountCreateWithoutUserInput = {
    id?: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token?: string | null
    access_token?: string | null
    expires_at?: number | null
    token_type?: string | null
    scope?: string | null
    id_token?: string | null
    session_state?: string | null
  }

  export type AccountUncheckedCreateWithoutUserInput = {
    id?: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token?: string | null
    access_token?: string | null
    expires_at?: number | null
    token_type?: string | null
    scope?: string | null
    id_token?: string | null
    session_state?: string | null
  }

  export type AccountCreateOrConnectWithoutUserInput = {
    where: AccountWhereUniqueInput
    create: XOR<AccountCreateWithoutUserInput, AccountUncheckedCreateWithoutUserInput>
  }

  export type AccountCreateManyUserInputEnvelope = {
    data: AccountCreateManyUserInput | AccountCreateManyUserInput[]
  }

  export type SessionCreateWithoutUserInput = {
    id?: string
    sessionToken: string
    expires: Date | string
  }

  export type SessionUncheckedCreateWithoutUserInput = {
    id?: string
    sessionToken: string
    expires: Date | string
  }

  export type SessionCreateOrConnectWithoutUserInput = {
    where: SessionWhereUniqueInput
    create: XOR<SessionCreateWithoutUserInput, SessionUncheckedCreateWithoutUserInput>
  }

  export type SessionCreateManyUserInputEnvelope = {
    data: SessionCreateManyUserInput | SessionCreateManyUserInput[]
  }

  export type AccountUpsertWithWhereUniqueWithoutUserInput = {
    where: AccountWhereUniqueInput
    update: XOR<AccountUpdateWithoutUserInput, AccountUncheckedUpdateWithoutUserInput>
    create: XOR<AccountCreateWithoutUserInput, AccountUncheckedCreateWithoutUserInput>
  }

  export type AccountUpdateWithWhereUniqueWithoutUserInput = {
    where: AccountWhereUniqueInput
    data: XOR<AccountUpdateWithoutUserInput, AccountUncheckedUpdateWithoutUserInput>
  }

  export type AccountUpdateManyWithWhereWithoutUserInput = {
    where: AccountScalarWhereInput
    data: XOR<AccountUpdateManyMutationInput, AccountUncheckedUpdateManyWithoutUserInput>
  }

  export type AccountScalarWhereInput = {
    AND?: AccountScalarWhereInput | AccountScalarWhereInput[]
    OR?: AccountScalarWhereInput[]
    NOT?: AccountScalarWhereInput | AccountScalarWhereInput[]
    id?: StringFilter<"Account"> | string
    userId?: StringFilter<"Account"> | string
    type?: StringFilter<"Account"> | string
    provider?: StringFilter<"Account"> | string
    providerAccountId?: StringFilter<"Account"> | string
    refresh_token?: StringNullableFilter<"Account"> | string | null
    access_token?: StringNullableFilter<"Account"> | string | null
    expires_at?: IntNullableFilter<"Account"> | number | null
    token_type?: StringNullableFilter<"Account"> | string | null
    scope?: StringNullableFilter<"Account"> | string | null
    id_token?: StringNullableFilter<"Account"> | string | null
    session_state?: StringNullableFilter<"Account"> | string | null
  }

  export type SessionUpsertWithWhereUniqueWithoutUserInput = {
    where: SessionWhereUniqueInput
    update: XOR<SessionUpdateWithoutUserInput, SessionUncheckedUpdateWithoutUserInput>
    create: XOR<SessionCreateWithoutUserInput, SessionUncheckedCreateWithoutUserInput>
  }

  export type SessionUpdateWithWhereUniqueWithoutUserInput = {
    where: SessionWhereUniqueInput
    data: XOR<SessionUpdateWithoutUserInput, SessionUncheckedUpdateWithoutUserInput>
  }

  export type SessionUpdateManyWithWhereWithoutUserInput = {
    where: SessionScalarWhereInput
    data: XOR<SessionUpdateManyMutationInput, SessionUncheckedUpdateManyWithoutUserInput>
  }

  export type SessionScalarWhereInput = {
    AND?: SessionScalarWhereInput | SessionScalarWhereInput[]
    OR?: SessionScalarWhereInput[]
    NOT?: SessionScalarWhereInput | SessionScalarWhereInput[]
    id?: StringFilter<"Session"> | string
    sessionToken?: StringFilter<"Session"> | string
    userId?: StringFilter<"Session"> | string
    expires?: DateTimeFilter<"Session"> | Date | string
  }

  export type FeedSyncCreateWithoutUserProfileInput = {
    id?: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    feedItems?: FeedItemCreateNestedManyWithoutFeedSyncInput
  }

  export type FeedSyncUncheckedCreateWithoutUserProfileInput = {
    id?: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    feedItems?: FeedItemUncheckedCreateNestedManyWithoutFeedSyncInput
  }

  export type FeedSyncCreateOrConnectWithoutUserProfileInput = {
    where: FeedSyncWhereUniqueInput
    create: XOR<FeedSyncCreateWithoutUserProfileInput, FeedSyncUncheckedCreateWithoutUserProfileInput>
  }

  export type FeedSyncCreateManyUserProfileInputEnvelope = {
    data: FeedSyncCreateManyUserProfileInput | FeedSyncCreateManyUserProfileInput[]
  }

  export type FeedSyncUpsertWithWhereUniqueWithoutUserProfileInput = {
    where: FeedSyncWhereUniqueInput
    update: XOR<FeedSyncUpdateWithoutUserProfileInput, FeedSyncUncheckedUpdateWithoutUserProfileInput>
    create: XOR<FeedSyncCreateWithoutUserProfileInput, FeedSyncUncheckedCreateWithoutUserProfileInput>
  }

  export type FeedSyncUpdateWithWhereUniqueWithoutUserProfileInput = {
    where: FeedSyncWhereUniqueInput
    data: XOR<FeedSyncUpdateWithoutUserProfileInput, FeedSyncUncheckedUpdateWithoutUserProfileInput>
  }

  export type FeedSyncUpdateManyWithWhereWithoutUserProfileInput = {
    where: FeedSyncScalarWhereInput
    data: XOR<FeedSyncUpdateManyMutationInput, FeedSyncUncheckedUpdateManyWithoutUserProfileInput>
  }

  export type FeedSyncScalarWhereInput = {
    AND?: FeedSyncScalarWhereInput | FeedSyncScalarWhereInput[]
    OR?: FeedSyncScalarWhereInput[]
    NOT?: FeedSyncScalarWhereInput | FeedSyncScalarWhereInput[]
    id?: StringFilter<"FeedSync"> | string
    userId?: StringFilter<"FeedSync"> | string
    feedType?: StringFilter<"FeedSync"> | string
    topicSlug?: StringNullableFilter<"FeedSync"> | string | null
    lastSyncAt?: DateTimeFilter<"FeedSync"> | Date | string
    nextSyncAt?: DateTimeNullableFilter<"FeedSync"> | Date | string | null
    isStale?: BoolFilter<"FeedSync"> | boolean
    syncInProgress?: BoolFilter<"FeedSync"> | boolean
    lastPage?: IntFilter<"FeedSync"> | number
    hasMore?: BoolFilter<"FeedSync"> | boolean
    totalItems?: IntNullableFilter<"FeedSync"> | number | null
    syncCount?: IntFilter<"FeedSync"> | number
    lastSyncDuration?: IntNullableFilter<"FeedSync"> | number | null
    lastError?: StringNullableFilter<"FeedSync"> | string | null
    consecutiveErrors?: IntFilter<"FeedSync"> | number
    createdAt?: DateTimeFilter<"FeedSync"> | Date | string
    updatedAt?: DateTimeFilter<"FeedSync"> | Date | string
  }

  export type FeedItemCreateWithoutArticleInput = {
    id?: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
    feedSync: FeedSyncCreateNestedOneWithoutFeedItemsInput
  }

  export type FeedItemUncheckedCreateWithoutArticleInput = {
    id?: string
    feedSyncId: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
  }

  export type FeedItemCreateOrConnectWithoutArticleInput = {
    where: FeedItemWhereUniqueInput
    create: XOR<FeedItemCreateWithoutArticleInput, FeedItemUncheckedCreateWithoutArticleInput>
  }

  export type FeedItemCreateManyArticleInputEnvelope = {
    data: FeedItemCreateManyArticleInput | FeedItemCreateManyArticleInput[]
  }

  export type FeedItemUpsertWithWhereUniqueWithoutArticleInput = {
    where: FeedItemWhereUniqueInput
    update: XOR<FeedItemUpdateWithoutArticleInput, FeedItemUncheckedUpdateWithoutArticleInput>
    create: XOR<FeedItemCreateWithoutArticleInput, FeedItemUncheckedCreateWithoutArticleInput>
  }

  export type FeedItemUpdateWithWhereUniqueWithoutArticleInput = {
    where: FeedItemWhereUniqueInput
    data: XOR<FeedItemUpdateWithoutArticleInput, FeedItemUncheckedUpdateWithoutArticleInput>
  }

  export type FeedItemUpdateManyWithWhereWithoutArticleInput = {
    where: FeedItemScalarWhereInput
    data: XOR<FeedItemUpdateManyMutationInput, FeedItemUncheckedUpdateManyWithoutArticleInput>
  }

  export type FeedItemScalarWhereInput = {
    AND?: FeedItemScalarWhereInput | FeedItemScalarWhereInput[]
    OR?: FeedItemScalarWhereInput[]
    NOT?: FeedItemScalarWhereInput | FeedItemScalarWhereInput[]
    id?: StringFilter<"FeedItem"> | string
    feedSyncId?: StringFilter<"FeedItem"> | string
    articleId?: StringFilter<"FeedItem"> | string
    position?: IntFilter<"FeedItem"> | number
    relevanceScore?: FloatNullableFilter<"FeedItem"> | number | null
    addedAt?: DateTimeFilter<"FeedItem"> | Date | string
  }

  export type LocalUserProfileCreateWithoutFeedSyncsInput = {
    id?: string
    userId: string
    publicId: string
    email: string
    name: string
    hasCompletedOnboarding?: boolean
    topics: string
    topicsDetails?: string | null
    regions: string
    languages: string
    publications: string
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type LocalUserProfileUncheckedCreateWithoutFeedSyncsInput = {
    id?: string
    userId: string
    publicId: string
    email: string
    name: string
    hasCompletedOnboarding?: boolean
    topics: string
    topicsDetails?: string | null
    regions: string
    languages: string
    publications: string
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type LocalUserProfileCreateOrConnectWithoutFeedSyncsInput = {
    where: LocalUserProfileWhereUniqueInput
    create: XOR<LocalUserProfileCreateWithoutFeedSyncsInput, LocalUserProfileUncheckedCreateWithoutFeedSyncsInput>
  }

  export type FeedItemCreateWithoutFeedSyncInput = {
    id?: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
    article: LocalArticleCreateNestedOneWithoutFeedItemsInput
  }

  export type FeedItemUncheckedCreateWithoutFeedSyncInput = {
    id?: string
    articleId: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
  }

  export type FeedItemCreateOrConnectWithoutFeedSyncInput = {
    where: FeedItemWhereUniqueInput
    create: XOR<FeedItemCreateWithoutFeedSyncInput, FeedItemUncheckedCreateWithoutFeedSyncInput>
  }

  export type FeedItemCreateManyFeedSyncInputEnvelope = {
    data: FeedItemCreateManyFeedSyncInput | FeedItemCreateManyFeedSyncInput[]
  }

  export type LocalUserProfileUpsertWithoutFeedSyncsInput = {
    update: XOR<LocalUserProfileUpdateWithoutFeedSyncsInput, LocalUserProfileUncheckedUpdateWithoutFeedSyncsInput>
    create: XOR<LocalUserProfileCreateWithoutFeedSyncsInput, LocalUserProfileUncheckedCreateWithoutFeedSyncsInput>
    where?: LocalUserProfileWhereInput
  }

  export type LocalUserProfileUpdateToOneWithWhereWithoutFeedSyncsInput = {
    where?: LocalUserProfileWhereInput
    data: XOR<LocalUserProfileUpdateWithoutFeedSyncsInput, LocalUserProfileUncheckedUpdateWithoutFeedSyncsInput>
  }

  export type LocalUserProfileUpdateWithoutFeedSyncsInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    publicId?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    hasCompletedOnboarding?: BoolFieldUpdateOperationsInput | boolean
    topics?: StringFieldUpdateOperationsInput | string
    topicsDetails?: NullableStringFieldUpdateOperationsInput | string | null
    regions?: StringFieldUpdateOperationsInput | string
    languages?: StringFieldUpdateOperationsInput | string
    publications?: StringFieldUpdateOperationsInput | string
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type LocalUserProfileUncheckedUpdateWithoutFeedSyncsInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    publicId?: StringFieldUpdateOperationsInput | string
    email?: StringFieldUpdateOperationsInput | string
    name?: StringFieldUpdateOperationsInput | string
    hasCompletedOnboarding?: BoolFieldUpdateOperationsInput | boolean
    topics?: StringFieldUpdateOperationsInput | string
    topicsDetails?: NullableStringFieldUpdateOperationsInput | string | null
    regions?: StringFieldUpdateOperationsInput | string
    languages?: StringFieldUpdateOperationsInput | string
    publications?: StringFieldUpdateOperationsInput | string
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemUpsertWithWhereUniqueWithoutFeedSyncInput = {
    where: FeedItemWhereUniqueInput
    update: XOR<FeedItemUpdateWithoutFeedSyncInput, FeedItemUncheckedUpdateWithoutFeedSyncInput>
    create: XOR<FeedItemCreateWithoutFeedSyncInput, FeedItemUncheckedCreateWithoutFeedSyncInput>
  }

  export type FeedItemUpdateWithWhereUniqueWithoutFeedSyncInput = {
    where: FeedItemWhereUniqueInput
    data: XOR<FeedItemUpdateWithoutFeedSyncInput, FeedItemUncheckedUpdateWithoutFeedSyncInput>
  }

  export type FeedItemUpdateManyWithWhereWithoutFeedSyncInput = {
    where: FeedItemScalarWhereInput
    data: XOR<FeedItemUpdateManyMutationInput, FeedItemUncheckedUpdateManyWithoutFeedSyncInput>
  }

  export type FeedSyncCreateWithoutFeedItemsInput = {
    id?: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
    userProfile: LocalUserProfileCreateNestedOneWithoutFeedSyncsInput
  }

  export type FeedSyncUncheckedCreateWithoutFeedItemsInput = {
    id?: string
    userId: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type FeedSyncCreateOrConnectWithoutFeedItemsInput = {
    where: FeedSyncWhereUniqueInput
    create: XOR<FeedSyncCreateWithoutFeedItemsInput, FeedSyncUncheckedCreateWithoutFeedItemsInput>
  }

  export type LocalArticleCreateWithoutFeedItemsInput = {
    id?: string
    backendId: string
    title: string
    visualTitle?: string | null
    description: string
    content?: string | null
    url: string
    imageUrl?: string | null
    publishedAt: Date | string
    readTime?: number | null
    isTopHeadline?: boolean
    sourceName: string
    sourceLogoUrl?: string | null
    summary?: string | null
    richContent?: string | null
    contentStatus?: string | null
    contentQuality?: string | null
    topics?: string | null
    isRead?: boolean
    isSaved?: boolean
    readAt?: Date | string | null
    savedAt?: Date | string | null
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type LocalArticleUncheckedCreateWithoutFeedItemsInput = {
    id?: string
    backendId: string
    title: string
    visualTitle?: string | null
    description: string
    content?: string | null
    url: string
    imageUrl?: string | null
    publishedAt: Date | string
    readTime?: number | null
    isTopHeadline?: boolean
    sourceName: string
    sourceLogoUrl?: string | null
    summary?: string | null
    richContent?: string | null
    contentStatus?: string | null
    contentQuality?: string | null
    topics?: string | null
    isRead?: boolean
    isSaved?: boolean
    readAt?: Date | string | null
    savedAt?: Date | string | null
    lastSyncAt?: Date | string
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type LocalArticleCreateOrConnectWithoutFeedItemsInput = {
    where: LocalArticleWhereUniqueInput
    create: XOR<LocalArticleCreateWithoutFeedItemsInput, LocalArticleUncheckedCreateWithoutFeedItemsInput>
  }

  export type FeedSyncUpsertWithoutFeedItemsInput = {
    update: XOR<FeedSyncUpdateWithoutFeedItemsInput, FeedSyncUncheckedUpdateWithoutFeedItemsInput>
    create: XOR<FeedSyncCreateWithoutFeedItemsInput, FeedSyncUncheckedCreateWithoutFeedItemsInput>
    where?: FeedSyncWhereInput
  }

  export type FeedSyncUpdateToOneWithWhereWithoutFeedItemsInput = {
    where?: FeedSyncWhereInput
    data: XOR<FeedSyncUpdateWithoutFeedItemsInput, FeedSyncUncheckedUpdateWithoutFeedItemsInput>
  }

  export type FeedSyncUpdateWithoutFeedItemsInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    userProfile?: LocalUserProfileUpdateOneRequiredWithoutFeedSyncsNestedInput
  }

  export type FeedSyncUncheckedUpdateWithoutFeedItemsInput = {
    id?: StringFieldUpdateOperationsInput | string
    userId?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type LocalArticleUpsertWithoutFeedItemsInput = {
    update: XOR<LocalArticleUpdateWithoutFeedItemsInput, LocalArticleUncheckedUpdateWithoutFeedItemsInput>
    create: XOR<LocalArticleCreateWithoutFeedItemsInput, LocalArticleUncheckedCreateWithoutFeedItemsInput>
    where?: LocalArticleWhereInput
  }

  export type LocalArticleUpdateToOneWithWhereWithoutFeedItemsInput = {
    where?: LocalArticleWhereInput
    data: XOR<LocalArticleUpdateWithoutFeedItemsInput, LocalArticleUncheckedUpdateWithoutFeedItemsInput>
  }

  export type LocalArticleUpdateWithoutFeedItemsInput = {
    id?: StringFieldUpdateOperationsInput | string
    backendId?: StringFieldUpdateOperationsInput | string
    title?: StringFieldUpdateOperationsInput | string
    visualTitle?: NullableStringFieldUpdateOperationsInput | string | null
    description?: StringFieldUpdateOperationsInput | string
    content?: NullableStringFieldUpdateOperationsInput | string | null
    url?: StringFieldUpdateOperationsInput | string
    imageUrl?: NullableStringFieldUpdateOperationsInput | string | null
    publishedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    readTime?: NullableIntFieldUpdateOperationsInput | number | null
    isTopHeadline?: BoolFieldUpdateOperationsInput | boolean
    sourceName?: StringFieldUpdateOperationsInput | string
    sourceLogoUrl?: NullableStringFieldUpdateOperationsInput | string | null
    summary?: NullableStringFieldUpdateOperationsInput | string | null
    richContent?: NullableStringFieldUpdateOperationsInput | string | null
    contentStatus?: NullableStringFieldUpdateOperationsInput | string | null
    contentQuality?: NullableStringFieldUpdateOperationsInput | string | null
    topics?: NullableStringFieldUpdateOperationsInput | string | null
    isRead?: BoolFieldUpdateOperationsInput | boolean
    isSaved?: BoolFieldUpdateOperationsInput | boolean
    readAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    savedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type LocalArticleUncheckedUpdateWithoutFeedItemsInput = {
    id?: StringFieldUpdateOperationsInput | string
    backendId?: StringFieldUpdateOperationsInput | string
    title?: StringFieldUpdateOperationsInput | string
    visualTitle?: NullableStringFieldUpdateOperationsInput | string | null
    description?: StringFieldUpdateOperationsInput | string
    content?: NullableStringFieldUpdateOperationsInput | string | null
    url?: StringFieldUpdateOperationsInput | string
    imageUrl?: NullableStringFieldUpdateOperationsInput | string | null
    publishedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    readTime?: NullableIntFieldUpdateOperationsInput | number | null
    isTopHeadline?: BoolFieldUpdateOperationsInput | boolean
    sourceName?: StringFieldUpdateOperationsInput | string
    sourceLogoUrl?: NullableStringFieldUpdateOperationsInput | string | null
    summary?: NullableStringFieldUpdateOperationsInput | string | null
    richContent?: NullableStringFieldUpdateOperationsInput | string | null
    contentStatus?: NullableStringFieldUpdateOperationsInput | string | null
    contentQuality?: NullableStringFieldUpdateOperationsInput | string | null
    topics?: NullableStringFieldUpdateOperationsInput | string | null
    isRead?: BoolFieldUpdateOperationsInput | boolean
    isSaved?: BoolFieldUpdateOperationsInput | boolean
    readAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    savedAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type AccountCreateManyUserInput = {
    id?: string
    type: string
    provider: string
    providerAccountId: string
    refresh_token?: string | null
    access_token?: string | null
    expires_at?: number | null
    token_type?: string | null
    scope?: string | null
    id_token?: string | null
    session_state?: string | null
  }

  export type SessionCreateManyUserInput = {
    id?: string
    sessionToken: string
    expires: Date | string
  }

  export type AccountUpdateWithoutUserInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type AccountUncheckedUpdateWithoutUserInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type AccountUncheckedUpdateManyWithoutUserInput = {
    id?: StringFieldUpdateOperationsInput | string
    type?: StringFieldUpdateOperationsInput | string
    provider?: StringFieldUpdateOperationsInput | string
    providerAccountId?: StringFieldUpdateOperationsInput | string
    refresh_token?: NullableStringFieldUpdateOperationsInput | string | null
    access_token?: NullableStringFieldUpdateOperationsInput | string | null
    expires_at?: NullableIntFieldUpdateOperationsInput | number | null
    token_type?: NullableStringFieldUpdateOperationsInput | string | null
    scope?: NullableStringFieldUpdateOperationsInput | string | null
    id_token?: NullableStringFieldUpdateOperationsInput | string | null
    session_state?: NullableStringFieldUpdateOperationsInput | string | null
  }

  export type SessionUpdateWithoutUserInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SessionUncheckedUpdateWithoutUserInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type SessionUncheckedUpdateManyWithoutUserInput = {
    id?: StringFieldUpdateOperationsInput | string
    sessionToken?: StringFieldUpdateOperationsInput | string
    expires?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedSyncCreateManyUserProfileInput = {
    id?: string
    feedType: string
    topicSlug?: string | null
    lastSyncAt: Date | string
    nextSyncAt?: Date | string | null
    isStale?: boolean
    syncInProgress?: boolean
    lastPage?: number
    hasMore?: boolean
    totalItems?: number | null
    syncCount?: number
    lastSyncDuration?: number | null
    lastError?: string | null
    consecutiveErrors?: number
    createdAt?: Date | string
    updatedAt?: Date | string
  }

  export type FeedSyncUpdateWithoutUserProfileInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedItems?: FeedItemUpdateManyWithoutFeedSyncNestedInput
  }

  export type FeedSyncUncheckedUpdateWithoutUserProfileInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedItems?: FeedItemUncheckedUpdateManyWithoutFeedSyncNestedInput
  }

  export type FeedSyncUncheckedUpdateManyWithoutUserProfileInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedType?: StringFieldUpdateOperationsInput | string
    topicSlug?: NullableStringFieldUpdateOperationsInput | string | null
    lastSyncAt?: DateTimeFieldUpdateOperationsInput | Date | string
    nextSyncAt?: NullableDateTimeFieldUpdateOperationsInput | Date | string | null
    isStale?: BoolFieldUpdateOperationsInput | boolean
    syncInProgress?: BoolFieldUpdateOperationsInput | boolean
    lastPage?: IntFieldUpdateOperationsInput | number
    hasMore?: BoolFieldUpdateOperationsInput | boolean
    totalItems?: NullableIntFieldUpdateOperationsInput | number | null
    syncCount?: IntFieldUpdateOperationsInput | number
    lastSyncDuration?: NullableIntFieldUpdateOperationsInput | number | null
    lastError?: NullableStringFieldUpdateOperationsInput | string | null
    consecutiveErrors?: IntFieldUpdateOperationsInput | number
    createdAt?: DateTimeFieldUpdateOperationsInput | Date | string
    updatedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemCreateManyArticleInput = {
    id?: string
    feedSyncId: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
  }

  export type FeedItemUpdateWithoutArticleInput = {
    id?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    feedSync?: FeedSyncUpdateOneRequiredWithoutFeedItemsNestedInput
  }

  export type FeedItemUncheckedUpdateWithoutArticleInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedSyncId?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemUncheckedUpdateManyWithoutArticleInput = {
    id?: StringFieldUpdateOperationsInput | string
    feedSyncId?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemCreateManyFeedSyncInput = {
    id?: string
    articleId: string
    position: number
    relevanceScore?: number | null
    addedAt?: Date | string
  }

  export type FeedItemUpdateWithoutFeedSyncInput = {
    id?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
    article?: LocalArticleUpdateOneRequiredWithoutFeedItemsNestedInput
  }

  export type FeedItemUncheckedUpdateWithoutFeedSyncInput = {
    id?: StringFieldUpdateOperationsInput | string
    articleId?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }

  export type FeedItemUncheckedUpdateManyWithoutFeedSyncInput = {
    id?: StringFieldUpdateOperationsInput | string
    articleId?: StringFieldUpdateOperationsInput | string
    position?: IntFieldUpdateOperationsInput | number
    relevanceScore?: NullableFloatFieldUpdateOperationsInput | number | null
    addedAt?: DateTimeFieldUpdateOperationsInput | Date | string
  }



  /**
   * Batch Payload for updateMany & deleteMany & createMany
   */

  export type BatchPayload = {
    count: number
  }

  /**
   * DMMF
   */
  export const dmmf: runtime.BaseDMMF
}