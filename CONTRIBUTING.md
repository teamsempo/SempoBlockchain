# Contributing to semantic-release

As a contributor, here are the guidelines we would like you to follow:

- [Code of conduct](#code-of-conduct)
- [How can I contribute?](#how-can-i-contribute?)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Coding rules](#coding-rules)
- [Working with the code](#get-started)

We also recommend that you read [How to Contribute to Open Source](https://opensource.guide/how-to-contribute).

## Code of conduct

Please read and follow our [Code of conduct](CODE_OF_CONDUCT.md).

## How can I contribute?

- Improve documentation
- Give feedback on issues
- Fix bugs and implement new features
- [Bug report](https://github.com/teamsempo/SempoBlockchain/issues/new?assignees=&labels=&template=bug_report.md&title=)
- [Feature request](https://github.com/teamsempo/SempoBlockchain/issues/new?assignees=&labels=&template=feature_request.md&title=)

## Submitting a Pull Request

TODO

## Coding rules

### Source code

TODO

### Documentation

TODO

### Commit message guidelines

#### Atomic commits

If possible, make [atomic commits](https://en.wikipedia.org/wiki/Atomic_commit), which means:

- a commit should contain exactly one self-contained functional change
- a functional change should be contained in exactly one commit
- a commit should not create an inconsistent state (such as test errors, linting errors, partial fix, feature with documentation etc...)

A complex feature can be broken down into multiple commits as long as each one maintains a consistent state and consists of a self-contained change.

#### Commit message format

We follow [Conventional Commits specifications](https://www.conventionalcommits.org/en/v1.0.0/)

The commit message should be structured as follows:

```commit
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

The **header** is mandatory and the **scope** of the header is optional.

The **footer** can contain a [closing reference to an issue](https://help.github.com/articles/closing-issues-via-commit-messages).

#### Revert

If the commit reverts a previous commit, it should begin with `revert:`, followed by the header of the reverted commit. In the body it should say: `This reverts commit <hash>.`, where the hash is the SHA of the commit being reverted.

#### Type

The type must be one of the following:

| Type         | Description                                                                                                 |
| ------------ | ----------------------------------------------------------------------------------------------------------- |
| **build**    | Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)         |
| **ci**       | Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs) |
| **docs**     | Documentation only changes                                                                                  |
| **feat**     | A new feature                                                                                               |
| **fix**      | A bug fix                                                                                                   |
| **perf**     | A code change that improves performance                                                                     |
| **refactor** | A code change that neither fixes a bug nor adds a feature                                                   |
| **style**    | Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)      |
| **test**     | Adding missing tests or correcting existing tests                                                           |

#### Subject

The subject contains succinct description of the change:

- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize first letter
- no dot (.) at the end

#### Body

Just as in the **subject**, use the imperative, present tense: "change" not "changed" nor "changes".
The body should include the motivation for the change and contrast this with previous behavior.

#### Footer

The footer should contain any information about **Breaking Changes** and is also the place to reference GitHub issues that this commit **Closes**.

**Breaking Changes** should start with the word `BREAKING CHANGE:` with a space or two newlines. The rest of the commit message is then used for this.

#### Examples

```commit
`fix(pencil): stop graphite breaking when too much pressure applied`
```

```commit
`feat(pencil): add 'graphiteWidth' option`

Fix #42
```

```commit
perf(pencil): remove graphiteWidth option`

BREAKING CHANGE: The graphiteWidth option has been removed.

The default graphite width of 10mm is always used for performance reasons.
```

## Get Started

TODO

### Lint / Code Formatter

TODO

### Tests

TODO
